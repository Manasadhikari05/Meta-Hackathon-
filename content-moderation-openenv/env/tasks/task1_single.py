# task1_single.py  ── Easy
from env.tasks.data import build_observation, load_posts

TASK_ID = "task1"
_INSTRUCTIONS = (
    "Moderate this post: choose approve, remove, or escalate with reason_code, "
    "severity, and confidence per policy."
)


class Task1:
    """One clear-cut post per episode. Grader: decision + reason_code."""

    def reset(self):
        self._posts = load_posts(difficulty="easy")
        self._current = self._posts.pop(0)
        return self._build_obs(step=0)

    def step(self, action):
        from env.graders.grader1 import grade

        reward = grade(action, self._current["gold_label"])
        done = True  # Task 1: one post per episode
        return reward, done, {"post_id": self._current["post_id"]}

    def current_observation(self):
        return self._build_obs(step=1)

    def _build_obs(self, step: int):
        return build_observation(TASK_ID, step, self._current, _INSTRUCTIONS)