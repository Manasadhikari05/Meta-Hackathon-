# task3 — 12 hard edge cases (sarcasm, obfuscation, etc)
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
        from env.graders.grader3 import grade

        post = self._posts[self._idx]
        score = grade(action, post["gold_label"])
        self._scores.append(score)
        self._idx += 1
        done = self._idx >= self.MAX_STEPS
        avg = sum(self._scores) / len(self._scores)
        avg = min(0.999, max(0.001, avg))
        return avg, done, {"completed": self._idx}

    def current_observation(self):
        # after last step, just return the final post again
        if self._idx >= len(self._posts):
            return build_observation(TASK_ID, self.MAX_STEPS, self._posts[-1], _INSTRUCTIONS)
        return build_observation(TASK_ID, self._idx, self._posts[self._idx], _INSTRUCTIONS)

    def _build_obs(self):
        return build_observation(TASK_ID, self._idx, self._posts[self._idx], _INSTRUCTIONS)