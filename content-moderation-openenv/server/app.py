import threading

from fastapi import FastAPI
from env.env import ContentModerationEnv
from env.models import ModerationAction

app = FastAPI(title="Content Moderation OpenEnv")

# Thread-safe lock to protect the single shared environment instance
_lock = threading.Lock()
env = ContentModerationEnv()


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/reset")
def reset(task_id: str = "task1"):
    with _lock:
        try:
            obs = env.reset(task_id)
            return obs.model_dump()
        except Exception as e:
            return {"error": str(e)}


@app.post("/step")
def step(action: ModerationAction):
    with _lock:
        try:
            obs, reward, done, info = env.step(action)
            return {
                "observation": obs.model_dump(),
                "reward": reward.model_dump(),
                "done": done,
                "info": info,
            }
        except Exception as e:
            return {"error": str(e)}


@app.get("/state")
def state():
    with _lock:
        try:
            return env.state()
        except Exception as e:
            return {"error": str(e)}