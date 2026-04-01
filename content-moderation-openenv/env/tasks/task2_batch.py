# task2_batch.py  ── Medium
from env.tasks.data import build_observation, load_posts

TASK_ID = "task2"
_INSTRUCTIONS = (
    "Moderate each post in the batch. Borderline toxicity may warrant escalation."
)


class Task2:
    """8-post batch. Agent processes one at a time. Rewards accumulate."""

    MAX_STEPS = 8

    def reset(self):
        self._posts = load_posts(difficulty="medium")[:8]
        self._index = 0
        self._episode_rewards = []
        return self._build_obs()

    def step(self, action):
        from env.graders.grader2 import grade

        post = self._posts[self._index]
        step_reward = grade(action, post["gold_label"])
        self._episode_rewards.append(step_reward)
        self._index += 1
        done = self._index >= self.MAX_STEPS
        avg_reward = sum(self._episode_rewards) / len(self._episode_rewards)
        return avg_reward, done, {"completed": self._index}

    def current_observation(self):
        if not self._posts:
            raise RuntimeError("Task2 has no posts loaded.")
        if self._index < len(self._posts):
            post = self._posts[self._index]
        else:
            post = self._posts[-1]
        step = min(self._index, self.MAX_STEPS)
        return build_observation(TASK_ID, step, post, _INSTRUCTIONS)

    def _build_obs(self):
        return build_observation(TASK_ID, self._index, self._posts[self._index], _INSTRUCTIONS)