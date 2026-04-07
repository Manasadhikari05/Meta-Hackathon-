import random
from typing import Tuple

from env.models import (
    ModerationAction,
    ModerationObservation,
    ModerationReward,
)
from env.tasks.task1_single import Task1
from env.tasks.task2_batch import Task2
from env.tasks.task3_edge import Task3

TASKS = {
    "task1": Task1,
    "task2": Task2,
    "task3": Task3,
}


class ContentModerationEnv:
    def __init__(self, task_id: str = "task1", seed: int = 42):
        self.seed = seed
        self._task = None
        self._step_count = 0
        self._done = False
        self._state = {}

        self._set_task(task_id)

    def _set_task(self, task_id: str):
        if task_id not in TASKS:
            raise ValueError(f"Invalid task_id: {task_id}")
        self.task_id = task_id
        self._task = TASKS[task_id]()

    def reset(self, task_id: str = None) -> ModerationObservation:
        """Reset env. Optionally switch tasks."""
        if task_id:
            self._set_task(task_id)

        random.seed(self.seed)
        self._step_count = 0
        self._done = False

        obs = self._task.reset()
        self._state = {
            "task_id": self.task_id,
            "step": 0,
            "obs": obs.model_dump(),
        }
        return obs

    def step(self, action) -> Tuple[ModerationObservation, ModerationReward, bool, dict]:
        if self._done:
            raise RuntimeError("Episode is done. Call reset() first.")

        # accept raw dict from the API layer
        if isinstance(action, dict):
            action = ModerationAction(**action)

        raw_reward, done, info = self._task.step(action)

        self._step_count += 1
        self._done = done

        value = float(raw_reward)
        value = min(0.99, max(0.01, value))
        reward = ModerationReward(
            value=value,
            breakdown={"scalar": value},
            done=done,
            info=info,
        )

        next_obs = self._task.current_observation()
        self._state["step"] = self._step_count
        self._state["obs"] = next_obs.model_dump()

        return next_obs, reward, done, info

    def state(self) -> dict:
        return {
            "task_id": self.task_id,
            "step": self._step_count,
            "done": self._done,
            "current_post_id": self._state.get("obs", {})
            .get("post", {})
            .get("post_id"),
        }