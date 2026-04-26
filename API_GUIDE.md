# Content Moderation OpenEnv — API Guide

The server has several APIs on the same FastAPI app:

- **AI Moderator** (`/moderate`, `/feedback`, `/history`) — llama3.2 reads user-submitted content and makes a moderation decision. Users then rate the AI's call 1–10.
- **RL Task Runner** (`/reset`, `/step`, `/state`) — a stateful gym-style environment where an agent moderates posts and gets scored by llama3.2 as judge.
- **RL training metrics** (`GET /training/metrics`) — JSON written by `RLtrainer.ipynb` or `python scripts/rl_trainer.py eval-comparison` into `results/rl_training_metrics.json` for the frontend before/after charts.

Base URL: `http://localhost:7860`

---

## Quick start

```bash
# 1. Make sure Ollama is running and llama3.2 is pulled
ollama serve          # starts the Ollama daemon
ollama pull llama3.2  # first time only

# 2. Start the backend
uv run uvicorn server.app:app --host 0.0.0.0 --port 7860

# 3. Open the frontend
cd frontend && npm run dev   # → http://localhost:5173
```

---

## Endpoints

### `GET /` · `GET /health`

Health check.

```json
{ "status": "ok" }
```

---

## AI Moderator endpoints

These are the main user-facing endpoints. The AI reads the content and makes a moderation call; the user rates it.

---

### `POST /moderate`

Submit any text. llama3.2 returns a full moderation decision.

**Request body**

```json
{
  "content": "buy followers cheap 10k for $5 DM now!!!",
  "platform": "social_media"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `content` | string | yes | 1–2000 characters |
| `platform` | string | no | Default `"social_media"`. Any of: `social_media` · `community_forum` · `marketplace` · `messaging` · `news_comments` |

**Response**

```json
{
  "post_id": "1544d884",
  "content": "buy followers cheap 10k for $5 DM now!!!",
  "platform": "social_media",
  "decision": "remove",
  "reason_code": "spam",
  "severity": "low",
  "confidence": 0.8,
  "explanation": "The post promotes the purchase of followers, which is spam.",
  "model": "llama3.2:latest"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `post_id` | string | Short unique ID for this moderation event |
| `decision` | string | `"approve"` · `"remove"` · `"escalate"` |
| `reason_code` | string | See reason codes below |
| `severity` | string | `"low"` · `"medium"` · `"high"` |
| `confidence` | float | 0.0–1.0 — how sure the AI is |
| `explanation` | string | One-sentence plain-English reasoning |
| `model` | string | Model that made the decision |

**Reason codes**

| Code | When used |
|------|-----------|
| `clean` | No issues — safe to approve |
| `spam` | Promotional, repetitive, or scam content |
| `hate_speech` | Attacks based on race, religion, gender, etc. |
| `harassment` | Targeted insults or threats at a specific person |
| `misinformation` | False or deliberately misleading claims |
| `self_harm` | Content promoting self-harm or suicide |
| `violence` | Violent threats, instructions, or graphic depictions |
| `sexual_content` | Explicit sexual material |

**Error** — `503` if Ollama is unreachable.

```bash
curl -X POST http://localhost:7860/moderate \
  -H "Content-Type: application/json" \
  -d '{"content": "just had the best coffee downtown!", "platform": "social_media"}'
```

---

### `POST /feedback`

Store a user's 1–10 rating of the AI's moderation decision. Pass back the full `/moderate` response plus `rating` and optional `comment`.

**Request body**

```json
{
  "post_id": "1544d884",
  "content": "buy followers cheap 10k for $5 DM now!!!",
  "platform": "social_media",
  "decision": "remove",
  "reason_code": "spam",
  "severity": "low",
  "confidence": 0.8,
  "explanation": "The post promotes the purchase of followers, which is spam.",
  "model": "llama3.2:latest",
  "rating": 9,
  "comment": "Correct — obvious spam, good call."
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `post_id` … `model` | — | yes | Echo back the fields from `/moderate` |
| `rating` | int | yes | 1 (terrible) to 10 (perfect) |
| `comment` | string | no | Optional free-text feedback |

**Response**

```json
{ "stored": true, "total": 1 }
```

```bash
curl -X POST http://localhost:7860/feedback \
  -H "Content-Type: application/json" \
  -d '{"post_id":"1544d884","content":"buy followers...","platform":"social_media","decision":"remove","reason_code":"spam","severity":"low","confidence":0.8,"explanation":"spam","model":"llama3.2:latest","rating":9}'
```

---

### `GET /history`

Return all past moderation decisions with user ratings, newest first.

**Response**

```json
[
  {
    "post_id": "1544d884",
    "content": "buy followers cheap 10k for $5 DM now!!!",
    "platform": "social_media",
    "decision": "remove",
    "reason_code": "spam",
    "severity": "low",
    "confidence": 0.8,
    "explanation": "The post promotes the purchase of followers, which is spam.",
    "model": "llama3.2:latest",
    "rating": 9,
    "comment": "Correct — obvious spam, good call."
  }
]
```

> Note: history is in-memory only and resets when the server restarts.

```bash
curl http://localhost:7860/history
```

---

## RL Task Runner endpoints

### `GET /reset` · `POST /reset`

Start or restart an episode. Optionally switch to a different task.

**Query parameter**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `task_id` | string | `"task1"` | `task1` · `task2` · `task3` |

**Example**
```bash
curl -X POST "http://localhost:7860/reset?task_id=task2"
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

Submit a moderation decision. The backend sends the full post context, your decision, and the gold-standard answer to **llama3.2**, which returns a score and a one-sentence explanation of that score.

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
| `confidence` | float | yes | `0.0 – 1.0` |
| `explanation` | string | no* | Your reasoning. **Required for task3** (AI grades it). Shown alongside the AI verdict in the UI for all tasks. |

**Response**

```json
{
  "observation": { "...": "next ModerationObservation" },
  "reward": {
    "value": 0.98,
    "breakdown": { "scalar": 0.98 },
    "done": true,
    "info": {}
  },
  "done": true,
  "info": {
    "post_id": "p_001",
    "reasoning": "Decision exactly matches gold standard; spam is correctly identified with high severity.",
    "ai_graded": true,
    "model": "llama3.2"
  }
}
```

Key fields in `info`:

| Field | Type | Description |
|-------|------|-------------|
| `post_id` | string | ID of the post that was just graded |
| `reasoning` | string | LLM's one-sentence explanation of the score |
| `ai_graded` | bool | `true` when Ollama graded it; `false` means heuristic fallback was used |
| `model` | string | Model that produced the score (`"llama3.2"`) |
| `completed` | int | (task2/task3 only) Steps completed so far |

`observation` is the next `ModerationObservation` — same schema as `/reset`. When `done` is `true` call `/reset` to begin a new episode.

---

### `GET /state`

Current episode snapshot without advancing. Good for debugging.

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
| `task2` | 8 | Medium | Batch. Borderline content; confidence calibration rewarded. |
| `task3` | 12 | Hard | Sarcasm, obfuscation, implicit harm. `explanation` is required and AI-scored. |

---

## AI Grading Engine

All scoring is done by **llama3.2 (3.2B Q4_K_M)** running locally via [Ollama](https://ollama.com). There are no hardcoded rule weights — the LLM reasons about the post content, author context, and your decision, then produces a score in (0, 1) with a human-readable justification.

### How the prompt works

The LLM receives:
- The full post content, platform, and topic
- Author risk signals (account age, prior violations, total posts)
- Your submitted decision (action, reason code, severity, confidence, explanation)
- The gold-standard correct answer
- A rubric that mirrors the original heuristic weights (decision 50%, reason 30%, severity 20%)

The LLM may award partial credit for semantically adjacent decisions (e.g. `escalate` when `remove` was correct) or equivalent reason codes (e.g. `harassment` ≈ `abuse`). It can also pick up on nuance that hardcoded rules miss — sarcasm, implied threat, cultural context.

### Task-specific grading

| Task | Extra grading notes |
|------|---------------------|
| `task1` | Straightforward. Rubric applied directly. |
| `task2` | Confidence calibration: high confidence on a correct decision earns a bonus; high confidence on a wrong one is penalised. |
| `task3` | Explanation quality adds up to 30% of the score. The LLM checks keyword overlap and coherence with the gold explanation. |

### Fallback

If Ollama is unreachable or returns invalid JSON, the server automatically falls back to the original heuristic graders (grader1/2/3). The `ai_graded` field in `info` will be `false` and `reasoning` will say `"Scored by heuristic grader (Ollama unavailable)."`.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API base URL |
| `AI_GRADER_MODEL` | `llama3.2:latest` | Model to use for grading |
| `AI_GRADER_TIMEOUT` | `60` | Request timeout in seconds |

Set these in `.env` (copy from `.env.example`).

---

## Scoring rubric (used in the LLM prompt)

| Component | Weight | Full credit | Partial credit |
|-----------|-------:|-------------|----------------|
| `decision` | 50% | Exact match | +0.20 if adjacent (remove↔escalate or approve↔escalate) |
| `reason_code` | 30% | Exact / semantic match | +0.12 if same broad category (abuse/spam/harm/safe) |
| `severity` | 20% | Exact match | +0.10 if off by one level |
| `confidence` | 10% | task2 only: ×confidence if correct | ×(1−confidence) if wrong |
| `explanation` | up to +30% | task3 only: keyword overlap + coherence | Scaled by quality |

**Penalty:** −0.20 if `approve` on a post that should be `remove` with a serious reason (`hate_speech`, `violence`, `self_harm`…).

All scores are clamped to **(0.001, 0.999)** — never exactly 0 or 1.

---

## Typical session

```bash
# Reset to task3
curl -X POST "http://localhost:7860/reset?task_id=task3"

# Submit 12 decisions (example — first one)
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "remove",
    "reason_code": "hate_speech",
    "severity": "high",
    "confidence": 0.9,
    "explanation": "Post uses coded slurs targeting an ethnic group despite superficial politeness."
  }'
# → info.reasoning: "Decision and reason code match gold; explanation correctly identifies the obfuscated hate pattern."
# → reward.value: 0.94

# Check mid-run state
curl http://localhost:7860/state

# After done=true, start over
curl -X POST "http://localhost:7860/reset?task_id=task1"
```

---

## Schema reference

### `ModerationObservation`

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Active task |
| `step` | int | 0-indexed step counter |
| `post.post_id` | string | Unique post identifier |
| `post.platform` | string | e.g. `community_forum`, `social_media` |
| `post.content` | string | Raw text of the post |
| `author.account_age_days` | int | Days since account creation |
| `author.prior_violations` | int | Past policy violations |
| `author.total_posts` | int | Lifetime post count |
| `thread_context.topic` | string | Thread topic |
| `thread_context.reply_to_post_id` | string\|null | Parent post ID if a reply |
| `instructions` | string | Task-specific moderation instructions shown to the agent |

### `ModerationAction` (request body for `/step`)

| Field | Type | Notes |
|-------|------|-------|
| `decision` | `"approve"\|"remove"\|"escalate"` | Required |
| `reason_code` | string enum | Required. See allowed values above. |
| `severity` | `"low"\|"medium"\|"high"` | Required |
| `confidence` | float 0–1 | Required |
| `explanation` | string | Optional for task1/task2; required for task3. The AI reads this when scoring. |

### `ModerationReward` (inside `/step` response)

| Field | Type | Description |
|-------|------|-------------|
| `value` | float | Step score, strictly in (0.001, 0.999) |
| `breakdown` | object | `{ "scalar": <value> }` |
| `done` | bool | `true` when episode is finished |
| `info` | object | *(empty — metadata is in the top-level `info` field)* |

### Top-level `info` (in `/step` response)

| Field | Type | Description |
|-------|------|-------------|
| `post_id` | string | ID of the post just scored |
| `reasoning` | string | LLM's one-sentence explanation |
| `ai_graded` | bool | `false` if Ollama was unavailable and heuristic fallback was used |
| `model` | string | `"llama3.2"` |
| `completed` | int | (task2/task3) Steps completed in this episode |

---

## Error responses

| Status | When |
|--------|------|
| `422 Unprocessable Entity` | Invalid `task_id` on `/reset`, or malformed action body |
| `500 Internal Server Error` | Calling `/step` after episode is done without resetting |

---

## Discord moderation endpoints

The Discord bot auto-moderates new server messages using your existing moderation model, then you can override decisions via API.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | *(empty)* | Bot token from Discord Developer Portal |
| `DISCORD_MOD_LOG_CHANNEL_ID` | *(empty)* | Optional channel ID for escalated-message logs |

### `GET /discord/status`

Returns whether the bot is enabled/connected and how many messages are tracked.

### `GET /discord/reviews?pending_only=true`

Returns AI moderation records for Discord messages.

- `pending_only=true`: only escalated messages waiting review
- `pending_only=false`: all tracked records

### `POST /discord/review/{message_id}`

Applies a manual moderation decision to a Discord message.

```json
{
  "action": "delete"
}
```

Allowed `action` values:

- `accept` (keep the message, clear flag)
- `delete` (delete message from Discord)
- `escalate` (flag message with reaction)
- `flag` (alias of `escalate`)
