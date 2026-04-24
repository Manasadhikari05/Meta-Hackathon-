# Content Moderation OpenEnv — API Guide

The server exposes a stateful RL-style environment over HTTP. One episode = one task run. You call `/reset` to start, then `/step` repeatedly until `done` is `true`.

Base URL: `http://localhost:7860`

---

## Endpoints

### `GET /`
### `GET /health`

Health check.

**Response**
```json
{ "status": "ok" }
```

---

### `GET /reset` · `POST /reset`

Start (or restart) an episode. Optionally switch to a different task.

**Query parameter**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `task_id` | string | `"task1"` | Which task to run. One of `task1`, `task2`, `task3`. |

**Example**
```bash
curl "http://localhost:7860/reset?task_id=task2"
```

**Response — `ModerationObservation`**
```json
{
  "task_id": "task1",
  "step": 0,
  "post": {
    "post_id": "p_001",
    "platform": "community_forum",
    "content": "buy followers cheap bro 10k for $5. DM rn!!!"
  },
  "author": {
    "account_age_days": 3,
    "prior_violations": 2,
    "total_posts": 4
  },
  "thread_context": {
    "topic": "technology",
    "reply_to_post_id": null
  },
  "instructions": "Moderate this post: choose approve, remove, or escalate with reason_code, severity, and confidence per policy."
}
```

---

### `POST /step`

Submit a moderation decision for the current post and advance the episode.

**Request body — `ModerationAction`**

```json
{
  "decision": "remove",
  "reason_code": "spam",
  "severity": "high",
  "confidence": 0.95,
  "explanation": "Explicit spam promotion with follower-buying offer."
}
```

| Field | Type | Required | Allowed values |
|-------|------|----------|----------------|
| `decision` | string | yes | `approve` · `remove` · `escalate` |
| `reason_code` | string | yes | `hate_speech` · `harassment` · `spam` · `misinformation` · `self_harm` · `violence` · `sexual_content` · `clean` |
| `severity` | string | yes | `low` · `medium` · `high` |
| `confidence` | float | yes | `0.0 – 1.0` (inclusive) |
| `explanation` | string | no* | Short sentence. **Required for task3.** |

**Response**

```json
{
  "observation": { ... },
  "reward": {
    "value": 0.999,
    "breakdown": { "scalar": 0.999 },
    "done": true,
    "info": {}
  },
  "done": true,
  "info": { "post_id": "p_001" }
}
```

`observation` is the next `ModerationObservation` (same schema as `/reset`).
When `done` is `true` the episode is over — call `/reset` to begin a new one.

---

### `GET /state`

Snapshot of the current episode without advancing it. Useful for debugging.

**Response**

```json
{
  "task_id": "task2",
  "step": 3,
  "done": false,
  "current_post_id": "p_012"
}
```

---

## Tasks

| Task | Posts | Difficulty | Key difference |
|------|------:|------------|----------------|
| `task1` | 1 | Easy | Single clear-cut post. Done in one step. |
| `task2` | 8 | Medium | Batch loop. Borderline content; confidence matters. |
| `task3` | 12 | Hard | Sarcasm, obfuscation, implicit harm. `explanation` is required. |

---

## Scoring

Each `/step` returns a `reward.value` in **(0, 1)** — never exactly 0 or 1.

Scores are computed per task:

**task1 & task2**

| Component | Weight | Full credit if… |
|-----------|-------:|-----------------|
| `decision` | 50 % | Exact match |
| `reason_code` | 30 % | Exact match (partial credit for same family) |
| `severity` | 20 % | Exact match (partial credit for ±1 step off) |

Adjacent decisions (`remove` ↔ `escalate`, `escalate` ↔ `approve`) earn partial decision credit.

**task3** adds an explanation quality check on top of the above.

**Penalities**

- Approving a post that should be removed for a serious reason (`hate_speech`, `violence`, `self_harm`, etc.) subtracts 0.20 from the raw score.

---

## Typical session

```bash
# 1. Start a task-3 episode
curl "http://localhost:7860/reset?task_id=task3"

# 2. Submit decisions until done=true (12 steps)
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "remove",
    "reason_code": "hate_speech",
    "severity": "high",
    "confidence": 0.9,
    "explanation": "Post uses coded language to target an ethnic group."
  }'

# 3. Inspect episode state mid-run
curl http://localhost:7860/state

# 4. After done=true, reset for another run
curl "http://localhost:7860/reset?task_id=task1"
```

---

## Data schema reference

### `ModerationObservation`

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Active task (`task1`/`task2`/`task3`) |
| `step` | int | 0-indexed step counter |
| `post.post_id` | string | Unique post identifier |
| `post.platform` | string | e.g. `community_forum`, `social_media` |
| `post.content` | string | Raw text of the post |
| `author.account_age_days` | int | Days since account creation |
| `author.prior_violations` | int | Number of past policy violations |
| `author.total_posts` | int | Lifetime post count |
| `thread_context.topic` | string | Thread topic |
| `thread_context.reply_to_post_id` | string \| null | Parent post ID if a reply |
| `instructions` | string | Task-specific moderation instructions |

### `ModerationReward`

| Field | Type | Description |
|-------|------|-------------|
| `value` | float | Score for this step, strictly in (0, 1) |
| `breakdown` | object | Per-component scores (currently `{ "scalar": <value> }`) |
| `done` | bool | `true` when the episode is finished |
| `info` | object | Extra metadata (e.g. `post_id`, `completed` step count) |

---

## Error responses

| Status | When |
|--------|------|
| `422 Unprocessable Entity` | Invalid `task_id` on `/reset`, or malformed action body |
| `500 Internal Server Error` | Calling `/step` after episode is done without resetting |
