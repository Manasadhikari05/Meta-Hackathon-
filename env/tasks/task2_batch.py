# task2 — batch of 8 medium-difficulty posts
from env.graders._shared import _clamp
from env.tasks.data import build_observation, load_posts

TASK_ID = "task2"
_INSTRUCTIONS = (
    "Moderate each post in the batch. Borderline toxicity may warrant escalation."
)


class Task2:
    MAX_STEPS = 8

    def reset(self):
        self._posts = load_posts(difficulty="medium")[:self.MAX_STEPS]
        self._index = 0
        self._rewards = []
        return self._build_obs()

    def step(self, action):
        from env.graders.ai_grader import grade

        post = self._posts[self._index]
        r, reasoning = grade(action, post, task_id=TASK_ID)
        r = _clamp(float(r))
        self._rewards.append(r)
        self._index += 1
        done = self._index >= self.MAX_STEPS
        return r, done, {
            "completed": self._index,
            "post_id": post["post_id"],
            "reasoning": reasoning,
            "ai_graded": True,
            "model": "llama3.2",
        }

    def current_observation(self):
        idx = min(self._index, len(self._posts) - 1)
        return build_observation(TASK_ID, self._index, self._posts[idx], _INSTRUCTIONS)

    def _build_obs(self):
        return build_observation(TASK_ID, self._index, self._posts[self._index], _INSTRUCTIONS)