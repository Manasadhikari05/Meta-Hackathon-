from pydantic import BaseModel, Field
from typing import Literal, Optional

# ── Sub-models embedded in Observation ──────────────────────────────

class AuthorHistory(BaseModel):
    account_age_days: int
    prior_violations: int
    total_posts: int

class ThreadContext(BaseModel):
    topic: str
    reply_to_post_id: Optional[str] = None

class PostContent(BaseModel):
    post_id: str
    platform: str
    content: str

# ── Core OpenEnv models ──────────────────────────────────────────────

class ModerationObservation(BaseModel):
    task_id: str
    step: int
    post: PostContent
    author: AuthorHistory
    thread_context: ThreadContext
    instructions: str

class ModerationAction(BaseModel):
    decision: Literal["approve", "remove", "escalate"]
    reason_code: Literal[
        "hate_speech", "harassment", "spam",
        "misinformation", "self_harm", "violence",
        "sexual_content", "clean"
    ]
    severity: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: Optional[str] = None   # required only in Task 3

class ModerationReward(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    breakdown: dict    # {"decision": 0.5, "reason": 0.3, "severity": 0.2}
    done: bool
    info: dict         # {"post_id": ..., "gold_decision": ..., "step": ...}