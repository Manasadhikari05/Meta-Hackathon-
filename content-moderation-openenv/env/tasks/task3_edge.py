# task3_edge.py  ── Hard
from env.tasks.data import build_observation, load_posts

TASK_ID = "task3"
_INSTRUCTIONS = (
    "Hard moderation: obfuscation, sarcasm, and implicit harm. "
    "You must include explanation (one sentence) for every decision."
)


class Task3:
    """12 edge-case posts. Grader also scores explanation quality."""

    MAX_STEPS = 12

    def reset(self):
        self._posts = load_posts(difficulty="hard")[:12]
        self._index = 0
        self._episode_rewards = []
        return self._build_obs()

    def step(self, action):
        from env.graders.grader3 import grade

        post = self._posts[self._index]
        step_reward = grade(action, post["gold_label"])
        self._episode_rewards.append(step_reward)
        self._index += 1
        done = self._index >= self.MAX_STEPS
        avg_reward = sum(self._episode_rewards) / len(self._episode_rewards)
        return avg_reward, done, {"completed": self._index}

    def current_observation(self):
        if not self._posts:
            raise RuntimeError("Task3 has no posts loaded.")
        if self._index < len(self._posts):
            post = self._posts[self._index]
        else:
            post = self._posts[-1]
        step = min(self._index, self.MAX_STEPS)
        return build_observation(TASK_ID, step, post, _INSTRUCTIONS)

    def _build_obs(self):
        return build_observation(TASK_ID, self._index, self._posts[self._index], _INSTRUCTIONS)