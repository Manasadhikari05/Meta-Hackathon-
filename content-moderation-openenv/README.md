# Content Moderation OpenEnv

An OpenEnv-compliant content moderation environment built for the Meta Hackathon.

## Overview

This project poses content moderation as a sequential decision-making problem. An LLM agent receives posts with author context and thread metadata, then decides how to moderate each one. It is rewarded based on how closely its decisions match gold labels.

## Tasks

| Task | Difficulty | Posts | Grading |
|------|-----------|-------|---------|
| `task1` | Easy | 1 post per episode | Decision (50%) + Reason (30%) + Severity (20%) |
| `task2` | Medium | 8 posts per episode | Decision (40%) + Reason (35%) + Severity (15%) + Confidence (10%) |
| `task3` | Hard | 12 edge-case posts | 70% base + 30% explanation quality |

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and fill in your OPENAI_API_KEY and OPENAI_BASE_URL
```

## Running

```bash
# 1. Start the environment server
uvicorn server.app:app --reload

# 2. In another terminal, run the LLM baseline
python baseline_inference.py
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/reset?task_id=task1` | Start a new episode |
| POST | `/step` | Submit a moderation action |
| GET | `/state` | Current environment state |

## ModerationAction Schema

```json
{
  "decision": "approve | remove | escalate",
  "reason_code": "hate_speech | harassment | spam | misinformation | self_harm | violence | sexual_content | clean",
  "severity": "low | medium | high",
  "confidence": 0.0,
  "explanation": "optional string (required for task3)"
}
```

## Running Tests

```bash
pytest tests/ -v
```
