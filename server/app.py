import threading

from fastapi import FastAPI, HTTPException
from env.env import ContentModerationEnv
from env.models import ModerationAction

app = FastAPI(title="Content Moderation OpenEnv")

_lock = threading.Lock()
env = ContentModerationEnv()


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
                "reward": reward.model_dump(),
                "done": done,
                "info": info,
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