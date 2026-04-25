import json
import sys
import threading
import time
import uuid
import random
import re
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from env.env import ContentModerationEnv
from env.models import ModerationAction
from env import policy_engine

app = FastAPI(title="Content Moderation OpenEnv")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── RL environment (OpenEnv task runner) ──────────────────────────────────────
_lock = threading.Lock()
env   = ContentModerationEnv()
policy_engine.load_state()


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.api_route("/reset", methods=["GET", "POST"])
def reset(task_id: str = "task1"):
    with _lock:
        try:
            obs = env.reset(task_id)
            return obs.model_dump()
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))


@app.post("/step")
def step(action: ModerationAction):
    with _lock:
        try:
            obs, reward, done, info = env.step(action)
            return {
                "observation": obs.model_dump(),
                "reward":      reward.model_dump(),
                "done":        done,
                "info":        info,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
def state():
    with _lock:
        try:
            return env.state()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/posts")
def get_posts(limit: int = 20, difficulty: Optional[str] = None):
    """Return posts from the OpenEnv dataset, optionally filtered by difficulty."""
    try:
        data_path = Path(__file__).parent.parent / "data" / "posts.json"
        posts = json.loads(data_path.read_text(encoding="utf-8"))
        if difficulty:
            posts = [p for p in posts if p.get("difficulty") == difficulty]
        return {"posts": posts[:limit], "total": len(posts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats():
    """Aggregate stats across all OpenEnv posts — used by the frontend dashboard."""
    try:
        data_path = Path(__file__).parent.parent / "data" / "posts.json"
        posts = json.loads(data_path.read_text(encoding="utf-8"))
        decisions = [p["gold_label"]["decision"] for p in posts]
        difficulties = [p.get("difficulty", "unknown") for p in posts]
        return {
            "total":     len(posts),
            "approved":  decisions.count("approve"),
            "removed":   decisions.count("remove"),
            "escalated": decisions.count("escalate"),
            "by_difficulty": {
                d: difficulties.count(d) for d in set(difficulties)
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── AI Moderator (user-facing) ────────────────────────────────────────────────

class ModerateRequest(BaseModel):
    content:  str            = Field(..., min_length=1, max_length=2000)
    platform: Optional[str] = "social_media"


class FeedbackRequest(BaseModel):
    post_id:     str
    content:     str
    decision:    str
    reason_code: str
    severity:    str
    confidence:  float
    explanation: str
    model:       str
    rating:      int           = Field(..., ge=1, le=10)
    comment:     Optional[str] = None
    desired_decision: Optional[str] = Field(default=None, pattern="^(approve|remove|escalate)$")


_feedback_store: list[dict] = []
_live_sessions: dict[str, dict] = {}
_live_comment_pool = [
    "This tutorial is super helpful, thanks!",
    "You are so dumb lol",
    "Buy followers cheap, instant growth guaranteed.",
    "I disagree with this take but good effort.",
    "Everyone from that community is trash.",
    "Can someone explain this part better?",
    "Click this link for free crypto now!",
    "Great breakdown, learned a lot.",
    "This person should just disappear.",
    "I love this reel so much.",
]


def _fallback_moderate(content: str) -> dict:
    text = content.lower()
    if any(k in text for k in ["buy followers", "free crypto", "click this link", "guaranteed"]):
        return {
            "decision": "remove",
            "reason_code": "spam",
            "severity": "high",
            "confidence": 0.9,
            "explanation": "Likely spam or scam content.",
        }
    if any(k in text for k in ["dumb", "trash", "disappear", "everyone from that community"]):
        return {
            "decision": "remove",
            "reason_code": "harassment",
            "severity": "high",
            "confidence": 0.88,
            "explanation": "Contains personal abuse or hateful phrasing.",
        }
    if any(k in text for k in ["disagree", "explain", "helpful", "learned", "love"]):
        return {
            "decision": "approve",
            "reason_code": "clean",
            "severity": "low",
            "confidence": 0.8,
            "explanation": "Safe or constructive comment.",
        }
    return {
        "decision": "escalate",
        "reason_code": "harassment",
        "severity": "medium",
        "confidence": 0.55,
        "explanation": "Borderline content; review suggested.",
    }


def _apply_learning_rules(content: str, base: dict, rules: list[dict]) -> dict:
    lowered = content.lower()
    for rule in reversed(rules):
        if rule["keyword"] in lowered:
            base["decision"] = rule["decision"]
            if rule["decision"] == "approve":
                base["reason_code"] = "clean"
                base["severity"] = "low"
            elif rule["decision"] == "remove":
                if base["reason_code"] == "clean":
                    base["reason_code"] = "harassment"
                base["severity"] = "high"
            else:
                base["severity"] = "medium"
            base["explanation"] = f"Adjusted from feedback rule for '{rule['keyword']}'."
            base["confidence"] = min(0.99, float(base.get("confidence", 0.5)) + 0.1)
            break
    return base


def _extract_keyword(content: str) -> str:
    tokens = re.findall(r"[a-zA-Z]{4,}", content.lower())
    stop = {"this", "that", "with", "from", "have", "your", "just", "really", "super", "thanks"}
    tokens = [t for t in tokens if t not in stop]
    return tokens[0] if tokens else "comment"


class LiveStartRequest(BaseModel):
    post_url: Optional[str] = None
    post_caption: Optional[str] = "Live moderation demo post"


class LiveFeedbackRequest(BaseModel):
    session_id: str
    comment_id: str
    desired_decision: str = Field(..., pattern="^(approve|remove|escalate)$")
    rating: int = Field(..., ge=1, le=10)
    note: Optional[str] = None


@app.post("/moderate")
def moderate_content(req: ModerateRequest):
    """Have OpenAI moderate user-submitted content and return a full decision."""
    from env.moderator import moderate
    try:
        raw = moderate(req.content, req.platform or "social_media")
        return policy_engine.apply_policy(req.content, raw)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI moderator unavailable: {e}")


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """Store the user's 1–10 rating of the AI's moderation call."""
    payload = req.model_dump()
    learn_result = policy_engine.learn_from_feedback(payload)
    _feedback_store.append(payload)
    return {"stored": True, "total": len(_feedback_store), **learn_result}


@app.get("/history")
def get_history():
    """Return all past moderation decisions with user ratings, newest first."""
    return list(reversed(_feedback_store))


@app.get("/policy/stats")
def policy_stats():
    return policy_engine.get_stats()


@app.get("/policy/rules")
def policy_rules(limit: int = 50):
    return {"rules": policy_engine.get_rules(limit=limit)}


@app.post("/live-comments/start")
def live_comments_start(req: LiveStartRequest):
    session_id = str(uuid.uuid4())[:10]
    _live_sessions[session_id] = {
        "session_id": session_id,
        "post_url": req.post_url or "https://instagram.com/p/demo",
        "post_caption": req.post_caption or "Live moderation demo post",
        "comments": [],
        "rules": [],
        "last_emit_at": 0.0,
        "emitted": 0,
    }
    return {"session_id": session_id, "post_url": _live_sessions[session_id]["post_url"]}


@app.get("/live-comments/poll")
def live_comments_poll(session_id: str):
    session = _live_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    now = time.time()
    should_emit = (now - session["last_emit_at"]) >= 1.5 and session["emitted"] < 100
    if should_emit:
        raw = random.choice(_live_comment_pool)
        comment_id = str(uuid.uuid4())[:8]
        try:
            from env.moderator import moderate
            verdict = moderate(raw, "instagram")
            base = {
                "decision": verdict["decision"],
                "reason_code": verdict["reason_code"],
                "severity": verdict["severity"],
                "confidence": verdict["confidence"],
                "explanation": verdict["explanation"],
                "model": verdict.get("model", "gpt-4o-mini"),
            }
        except Exception:
            base = _fallback_moderate(raw)
            base["model"] = "fallback-heuristic"

        tuned = _apply_learning_rules(raw, base, session["rules"])
        item = {
            "comment_id": comment_id,
            "content": raw,
            "decision": tuned["decision"],
            "reason_code": tuned["reason_code"],
            "severity": tuned["severity"],
            "confidence": tuned["confidence"],
            "explanation": tuned["explanation"],
            "model": tuned["model"],
            "ts": int(now),
        }
        session["comments"].append(item)
        session["last_emit_at"] = now
        session["emitted"] += 1

    return {
        "session_id": session_id,
        "comments": session["comments"][-30:],
        "learning_rules": len(session["rules"]),
        "emitted": session["emitted"],
    }


@app.post("/live-comments/feedback")
def live_comments_feedback(req: LiveFeedbackRequest):
    session = _live_sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Unknown session_id")

    found = next((c for c in session["comments"] if c["comment_id"] == req.comment_id), None)
    if not found:
        raise HTTPException(status_code=404, detail="Unknown comment_id")

    keyword = _extract_keyword(found["content"])
    if req.rating <= 6 or found["decision"] != req.desired_decision:
        session["rules"].append(
            {
                "keyword": keyword,
                "decision": req.desired_decision,
                "rating": req.rating,
                "note": req.note,
                "created_at": int(time.time()),
            }
        )
    return {"stored": True, "keyword": keyword, "rules_total": len(session["rules"])}


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
