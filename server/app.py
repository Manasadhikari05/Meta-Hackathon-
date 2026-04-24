import threading
from typing import Optional

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

# ── RL environment (task runner) ─────────────────────────────────────────────
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


# ── AI Moderator ──────────────────────────────────────────────────────────────

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
    """Have llama3.2 moderate user-submitted content and return a full decision."""
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
