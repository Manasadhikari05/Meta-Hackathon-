---
title: Content Moderation
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Content Moderation OpenEnv

Hackathon submission — RL-style environment for content moderation.

An LLM agent reviews social media posts one at a time, classifies each one (approve / remove / escalate), and gets scored against gold labels.

## Tasks

| Task | Posts | Focus |
|------|-------|-------|
| task1 | 1 | Basic — decision + reason + severity |
| task2 | 8 | Batch — adds confidence calibration |
| task3 | 12 | Edge cases — sarcasm, obfuscation, implicit harm. Requires explanations. |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # add your API key + model

# start the env server
uvicorn server.app:app --host 0.0.0.0 --port 7860

# in another terminal, run the agent
python inference.py
```

## Docker

```bash
docker build -t cm-openenv .
docker run -p 7860:7860 cm-openenv
```

## API

| Method | Path | What you get |
|--------|------|-------------|
| GET | `/` | Health check |
| GET/POST | `/reset?task_id=task1` | First observation |
| POST | `/step` | Reward + next observation |
| GET | `/state` | Current episode snapshot |

### Action format

```json
{
  "decision": "approve | remove | escalate",
  "reason_code": "hate_speech | harassment | spam | misinformation | self_harm | violence | sexual_content | clean",
  "severity": "low | medium | high",
  "confidence": 0.85,
  "explanation": "short reason (task3 only)"
}
```

## Config

Set these in `.env`:

- `API_BASE_URL` — LLM endpoint (e.g. `https://api.groq.com/openai/v1`)
- `MODEL_NAME` — model to use (e.g. `llama-3.3-70b-versatile`)
- `HF_TOKEN` — API key

## Tests

```bash
pytest tests/ -v
```
