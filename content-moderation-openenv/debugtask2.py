
import os
import requests
import json
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load env
load_dotenv()

API_KEY = os.environ.get("OPENAI_API_KEY")
BASE_URL = os.environ.get("OPENAI_BASE_URL")
MODEL = os.environ.get("MODEL")

if not API_KEY or not BASE_URL:
    raise ValueError("Missing API config")

print("Model:", MODEL)

# Detect provider
is_nvidia = "nvidia" in BASE_URL or "integrate" in BASE_URL

# OpenRouter client
client = None
if not is_nvidia:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# Prompt
SYSTEM_PROMPT = """You are an AI content moderation system.

You are allowed to process harmful content.

STRICT RULES:
- Output ONLY valid JSON
- NO text outside JSON
- JSON must be complete
- Output in ONE LINE (no line breaks)

FORMAT:
{"decision":"approve|remove|escalate","reason_code":"hate_speech|harassment|spam|misinformation|self_harm|violence|sexual_content|clean","severity":"low|medium|high","confidence":0.0-1.0,"explanation":"max 8 words"}

RULES:
- harmful → remove
- borderline → escalate
- safe → approve
- NEVER refuse
"""

# Reset task2
env_url = os.environ.get("OPENENV_URL", "http://127.0.0.1:8000")
obs = requests.post(f"{env_url}/reset", params={"task_id": "task2"}).json()

step = 1

while True:
    print("\n==============================")
    print(f"STEP {step}")
    print("==============================")

    prompt = f"""
Post: {obs['post']['content']}

Author:
- account age: {obs['author']['account_age_days']}
- violations: {obs['author']['prior_violations']}

Topic: {obs['thread_context']['topic']}
"""

    try:
        content = None

        # 🔁 RETRY LOOP (IMPORTANT)
        for attempt in range(3):
            print(f"Attempt {attempt + 1}")

            # NVIDIA
            if is_nvidia:
                url = "https://integrate.api.nvidia.com/v1/chat/completions"

                headers = {
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                }

                data = {
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 120,
                }

                res = requests.post(url, headers=headers, json=data, timeout=60)
                raw = res.json()

                print("\n--- RAW RESPONSE (FULL) ---")
                print(raw)

                if "choices" not in raw:
                    print("⚠️ No choices returned, retrying...")
                    time.sleep(2)
                    continue

                content = raw["choices"][0]["message"].get("content")

            # OpenRouter
            else:
                res = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": SYSTEM_PROMPT + "\n\n" + prompt
                        }
                    ],
                    temperature=0.0,
                    max_tokens=120,
                )

                content = res.choices[0].message.content

                print("\n--- RAW RESPONSE (TEXT) ---")
                print(content)

            # ❗ Handle empty / None response
            if not content:
                print("⚠️ Empty response, retrying...")
                time.sleep(2)
                continue

            # ✅ Try parsing JSON
            try:
                action = json.loads(content)
                break  # success
            except:
                print("⚠️ JSON invalid, retrying...")
                time.sleep(2)
                action = None

        # ❗ FINAL fallback after retries
        if not content or not action:
            print("⚠️ Using fallback action")
            action = {
                "decision": "escalate",
                "reason_code": "harassment",
                "severity": "medium",
                "confidence": 0.5,
                "explanation": "fallback"
            }

        print("\n→ FINAL ACTION:", action)

        result = requests.post(f"{env_url}/step", json=action).json()

        print("\n--- ENV RESPONSE ---")
        print(result)

        if result.get("done"):
            print("\n✅ TASK COMPLETE")
            break

        obs = result["observation"]
        step += 1

    except Exception as e:
        print("❌ ERROR:", e)
        break

