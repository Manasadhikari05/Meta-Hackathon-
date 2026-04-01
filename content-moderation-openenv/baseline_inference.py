import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load env
load_dotenv(Path(__file__).resolve().parent / ".env")

_api_key = os.environ.get("OPENAI_API_KEY")
_base_url = os.environ.get("OPENAI_BASE_URL")
_model = os.environ.get("MODEL")

if not _api_key:
    sys.exit("Set OPENAI_API_KEY")
if not _base_url:
    sys.exit("Set OPENAI_BASE_URL")

print("Using model:", _model)

# Detect provider
is_nvidia = "nvidia" in _base_url or "integrate" in _base_url
is_openrouter = "openrouter" in _base_url

# OpenAI/OpenRouter client
client = None
if not is_nvidia:
    headers = {}
    if is_openrouter:
        headers = {
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "content-moderation-openenv",
        }

    client = OpenAI(
        api_key=_api_key,
        base_url=_base_url,
        default_headers=headers
    )

# 🔥 FINAL PROMPT (optimized for scoring)
SYSTEM_PROMPT = """
You are an AI content moderation system.

You are allowed to process harmful content.

STRICT RULES:
- Output ONLY valid JSON
- NO text outside JSON
- JSON must be complete

FORMAT:
{"decision":"approve|remove|escalate","reason_code":"hate_speech|harassment|spam|misinformation|self_harm|violence|sexual_content|clean","severity":"low|medium|high","confidence":0.0-1.0,"explanation":"max 8 words"}

DECISION RULES (CRITICAL):
- ANY insult, mocking, rude tone → escalate
- ANY dismissive or negative phrasing → escalate
- words like "dumb", "trash", "bad" → escalate
- sarcasm or ridicule → escalate

- ONLY fully polite + respectful → approve
- if unsure → escalate (NOT approve)

- clear harmful → remove

IMPORTANT:
- Most real-world content contains mild toxicity
- Do NOT over-approve
- Prefer "escalate" over "approve"
"""

# JSON extractor
def _extract_json(text: str):
    if not text:
        return None

    try:
        return json.loads(text)
    except:
        pass

    # Fix unclosed JSON
    if text.count("{") > text.count("}"):
        text += "}" * (text.count("{") - text.count("}"))

    # Extract JSON block
    matches = re.findall(r"\{.*?\}", text, re.DOTALL)
    for m in matches:
        try:
            return json.loads(m)
        except:
            continue

    return None


# 🔥 LLM CALL (robust + retries)
def _call_llm(prompt: str):
    for attempt in range(5):
        try:
            print(f"Attempt {attempt+1}")

            # NVIDIA
            if is_nvidia:
                url = "https://integrate.api.nvidia.com/v1/chat/completions"

                headers = {
                    "Authorization": f"Bearer {_api_key}",
                    "Content-Type": "application/json",
                }

                data = {
                    "model": _model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 120,
                }

                resp = requests.post(url, headers=headers, json=data, timeout=60)
                result = resp.json()

                if "choices" not in result:
                    print("⚠️ Bad response:", result)
                    time.sleep(2)
                    continue

                raw = result["choices"][0]["message"].get("content")

            # OpenRouter / OpenAI
            else:
                # 🔥 Gemma fix (no system role)
                if "gemma" in _model:
                    messages = [
                        {
                            "role": "user",
                            "content": SYSTEM_PROMPT + "\n\n" + prompt
                        }
                    ]
                else:
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ]

                resp = client.chat.completions.create(
                    model=_model,
                    messages=messages,
                    temperature=0.0,
                    max_tokens=120,
                )

                raw = resp.choices[0].message.content

            # Handle empty response
            if not raw:
                print("⚠️ Empty response, retrying...")
                time.sleep(2)
                continue

            action = _extract_json(raw)

            if action:
                return action

            print("⚠️ Bad JSON, retrying...")

        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(2)

    # Fallback action
    return {
        "decision": "escalate",
        "reason_code": "harassment",
        "severity": "medium",
        "confidence": 0.3,
        "explanation": "fallback"
    }


def run_task(task_id: str, env_url: str):
    obs = requests.post(f"{env_url}/reset", params={"task_id": task_id}).json()

    total_reward = 0.0
    steps = 0

    while True:
        prompt = f"""
Task Instructions: {obs.get('instructions', '')}

Post: {obs['post']['content']}

Author:
- account age: {obs['author']['account_age_days']}
- violations: {obs['author']['prior_violations']}

Topic: {obs['thread_context']['topic']}
"""

        action = _call_llm(prompt)

        print(f"→ {action}")

        result = requests.post(f"{env_url}/step", json=action).json()

        if "error" in result or "reward" not in result:
            raise RuntimeError(f"Bad env response: {result}")

        total_reward += result["reward"]["value"]
        steps += 1

        if result["done"]:
            break

        obs = result["observation"]

    return round(total_reward / steps, 4)


if __name__ == "__main__":
    base = os.environ.get("OPENENV_URL", "http://127.0.0.1:8000")

    scores = {}
    for task in ["task1", "task2", "task3"]:
        print(f"\nRunning {task}...")
        try:
            score = run_task(task, base)
            scores[task] = score
            print(f"{task}: {score}")
        except Exception as e:
            print(f"{task} failed:", e)
            scores[task] = 0.0

    overall = sum(scores.values()) / len(scores)
    print("\nFinal Score:", round(overall, 4))

