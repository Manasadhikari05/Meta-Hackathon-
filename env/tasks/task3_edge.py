# task3 — 12 hard edge cases (sarcasm, obfuscation, etc)
from env.graders._shared import _clamp
from env.tasks.data import build_observation, load_posts

TASK_ID = "task3"
_INSTRUCTIONS = (
    "Hard moderation: obfuscation, sarcasm, and implicit harm. "
    "You must include explanation (one sentence) for every decision."
)


class Task3:
    MAX_STEPS = 12

    def reset(self):
        self._posts = load_posts(difficulty="hard")[:self.MAX_STEPS]
        self._idx = 0
        self._scores = []
        return self._build_obs()

    def step(self, action):
        from env.graders.ai_grader import grade

        post = self._posts[self._idx]
        point_score, reasoning = grade(action, post, task_id=TASK_ID)
        point_score = _clamp(float(point_score))
        self._scores.append(point_score)
        self._idx += 1
        done = self._idx >= self.MAX_STEPS
        return point_score, done, {
            "completed": self._idx,
            "post_id": post["post_id"],
            "reasoning": reasoning,
            "ai_graded": True,
            "model": "llama3.2",
        }

    def current_observation(self):
        # after last step, just return the final post again
        if self._idx >= len(self._posts):
            return build_observation(TASK_ID, self.MAX_STEPS, self._posts[-1], _INSTRUCTIONS)
        return build_observation(TASK_ID, self._idx, self._posts[self._idx], _INSTRUCTIONS)

    def _build_obs(self):
        return build_observation(TASK_ID, self._idx, self._posts[self._idx], _INSTRUCTIONS)