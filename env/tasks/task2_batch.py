# task2 — batch of 8 medium-difficulty posts
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
        from env.graders.grader2 import grade

        post = self._posts[self._index]
        r = grade(action, post["gold_label"])
        self._rewards.append(r)
        self._index += 1
        done = self._index >= self.MAX_STEPS
        avg = sum(self._rewards) / len(self._rewards)
        avg = min(0.999, max(0.001, avg))
        return avg, done, {"completed": self._index}

    def current_observation(self):
        idx = min(self._index, len(self._posts) - 1)
        return build_observation(TASK_ID, self._index, self._posts[idx], _INSTRUCTIONS)

    def _build_obs(self):
        return build_observation(TASK_ID, self._index, self._posts[self._index], _INSTRUCTIONS)