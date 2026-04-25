# task1 — single post, easy
from env.graders._shared import _clamp
from env.tasks.data import build_observation, load_posts

TASK_ID = "task1"
_INSTRUCTIONS = (
    "Moderate this post: choose approve, remove, or escalate with reason_code, "
    "severity, and confidence per policy."
)


class Task1:
    """Single clear-cut post. Done after one step."""

    def reset(self):
        self._posts = load_posts(difficulty="easy")
        self._current = self._posts.pop(0)
        return self._build_obs(step=0)

    def step(self, action):
        from env.graders.ai_grader import grade

        score, reasoning = grade(action, self._current, task_id=TASK_ID)
        score = _clamp(float(score))
        return score, True, {
            "post_id": self._current["post_id"],
            "reasoning": reasoning,
            "ai_graded": True,
            "model": "gpt-4o-mini",
        }

    def current_observation(self):
        return self._build_obs(step=1)

    def _build_obs(self, step: int):
        return build_observation(TASK_ID, step, self._current, _INSTRUCTIONS)