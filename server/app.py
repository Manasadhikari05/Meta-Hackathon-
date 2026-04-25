import json
import sys
import threading
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


_feedback_store: list[dict] = []


@app.post("/moderate")
def moderate_content(req: ModerateRequest):
    """Have OpenAI moderate user-submitted content and return a full decision."""
    from env.moderator import moderate
    try:
        return moderate(req.content, req.platform or "social_media")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI moderator unavailable: {e}")


@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """Store the user's 1–10 rating of the AI's moderation call."""
    _feedback_store.append(req.model_dump())
    return {"stored": True, "total": len(_feedback_store)}


@app.get("/history")
def get_history():
    """Return all past moderation decisions with user ratings, newest first."""
    return list(reversed(_feedback_store))


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
