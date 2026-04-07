import pytest

from env.env import ContentModerationEnv
from env.models import ModerationAction


@pytest.fixture
def approve_clean():
    return ModerationAction(
        decision="approve",
        reason_code="clean",
        severity="low",
        confidence=0.9,
        explanation=None,
    )


def test_task1_basic(approve_clean):
    env = ContentModerationEnv(task_id="task1", seed=0)
    obs = env.reset()
    assert obs.task_id == "task1"
    assert obs.post.post_id
    _next_obs, reward, done, info = env.step(approve_clean)
    assert done is True
    assert 0.0 < reward.value < 1.0
    assert "post_id" in info


def test_task2_full_run(approve_clean):
    env = ContentModerationEnv(task_id="task2", seed=1)
    env.reset()
    done = False
    for _ in range(8):
        _obs, reward, done, _info = env.step(approve_clean)
        assert 0.0 < reward.value < 1.0
    assert done is True


def test_task3_all_steps(approve_clean):
    env = ContentModerationEnv(task_id="task3", seed=2)
    env.reset()
    action = approve_clean.model_copy(
        update={"explanation": "Borderline but appears policy-compliant."}
    )
    done = False
    n = 0
    while not done:
        _obs, _r, done, _info = env.step(action)
        n += 1
        assert n <= 12
    assert n == 12


def test_double_step_raises():
    env = ContentModerationEnv(task_id="task1", seed=3)
    env.reset()
    env.step(
        ModerationAction(
            decision="remove",
            reason_code="spam",
            severity="high",
            confidence=0.8,
        )
    )
    with pytest.raises(RuntimeError, match="Episode is done"):
        env.step(
            ModerationAction(
                decision="approve",
                reason_code="clean",
                severity="low",
                confidence=0.5,
            )
        )
