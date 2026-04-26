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
pip install transformers accelerate sentencepiece torch bitsandbytes
cp .env.example .env  # add your API key + model

# start the env server
uvicorn server.app:app --host 0.0.0.0 --port 7860

# in another terminal, run the agent (downloads local model automatically on first run)
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

- `USE_LOCAL_LLM` — Set to `true` (default) to run local HuggingFace inference, `false` to fallback to cloud API
- `HF_MODEL_ID` — Local HuggingFace model to use (e.g. `mistralai/Mistral-7B-Instruct-v0.2`)
- `OPENAI_API_KEY` — API key for ai_grader (and optional inference fallback)
- `MODEL_NAME` — Cloud model to use if `USE_LOCAL_LLM=false` (e.g. `gpt-4o-mini`)

## Tests

```bash
pytest tests/ -v
```

## RL-style training & before/after metrics

1. **Notebook:** open `RLtrainer.ipynb` at the repo root — evaluates the same Qwen policy as production on `data/posts.json`, writes **greedy vs best-of-N** curves to `results/rl_training_metrics.json`.
2. **CLI (same output):**  
   `python scripts/rl_trainer.py eval-comparison --best-of 4 --limit 40`
3. **Optional weight update (LoRA BC):** install extras `pip install -r requirements-train.txt`, then  
   `python scripts/rl_trainer.py lora-sft --output-dir ./output/qwen-mod-lora`  
   Set `HF_ADAPTER_PATH` in `.env` and restart uvicorn so `inference.py` merges the adapter.
4. **Frontend:** open **RL training results** from the landing header or dashboard — charts read `GET /training/metrics`.

*Best-of-N is test-time policy improvement (more forward passes, no gradient step). LoRA is supervised fine-tuning on gold labels — closer to offline RL / BC than online PPO.*
