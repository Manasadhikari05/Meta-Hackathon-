import json
from pathlib import Path

from env.models import AuthorHistory, ModerationObservation, PostContent, ThreadContext

_POSTS_PATH = Path(__file__).resolve().parents[2] / "data" / "posts.json"


def load_posts(difficulty: str) -> list[dict]:
    with open(_POSTS_PATH, encoding="utf-8") as f:
        posts = json.load(f)
    return [p for p in posts if p.get("task_difficulty") == difficulty]


def build_observation(task_id, step, post_row, instructions):
    tc = post_row["thread_context"]
    return ModerationObservation(
        task_id=task_id,
        step=step,
        post=PostContent(
            post_id=post_row["post_id"],
            platform=post_row["platform"],
            content=post_row["content"],
        ),
        author=AuthorHistory(**post_row["author"]),
        thread_context=ThreadContext(
            topic=tc["topic"],
            reply_to_post_id=tc.get("reply_to_post_id"),
        ),
        instructions=instructions,
    )
