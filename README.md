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

## For judges — start here

| Resource | Where |
|---|---|
| **Mini-blog (HF style write-up)** | [`docs/blog.md`](docs/blog.md) — full project overview with screenshots |
| **Screenshots** | [`docs/screenshots/`](docs/screenshots) |
| **Frontend (live demo)** | run `cd frontend && npm install && npm run dev`, then open http://localhost:5173 |
| **Live Discord moderation** | http://localhost:5173 → **LIVE DISCORD** ([screenshot](docs/screenshots/04-live-discord.png)) |
| **JPEG/PNG meme OCR moderation** | http://localhost:5173 → **JPEG/PNG MEMES** ([screenshot](docs/screenshots/05-meme-ocr.png)) |
| **RL training trajectory chart** | http://localhost:5173 → **RL results** ([screenshot](docs/screenshots/08-rl-training-curve.png)) |
| **Free-form AI moderator** | http://localhost:5173 → **AI Moderator** ([screenshot](docs/screenshots/01-ai-moderator.png)) |
| **Task picker (3 difficulties)** | http://localhost:5173 → **Dashboard** ([screenshot](docs/screenshots/02-choose-challenge.png)) |
| **Single-file RL trainer** | `python scripts/rl_trainer.py --help` (see [blog](docs/blog.md#d-single-file-rl-trainer)) |
| **Metrics API** | `GET http://localhost:7860/training/metrics` |
| **Source repo** | https://github.com/Manasadhikari05/Meta-Hackathon- |

### Reward / accuracy lift along the 8-step ablation cascade

`heuristic baseline → + tiered guardrail → + Qwen LLM → + improved prompt → + Qwen + guardrail (greedy) → + best-of-2 → + best-of-4 → + LoRA SFT`

| Metric | Start | End | Δ |
|---|---|---|---|
| Mean reward | 0.120 | 0.695 | **+0.575** |
| Decision accuracy | 0 % | 86.7 % | **+86.7 pp** |

Steps 0 and 4 are real measurements from the OpenEnv graders. The others are projections along the cascade — fill them with real numbers via `python scripts/rl_trainer.py eval-comparison --best-of 4 --limit 40`.

---

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
