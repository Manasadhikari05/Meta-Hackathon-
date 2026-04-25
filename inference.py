# inference.py — moderation agent
# talks to the env server, classifies posts via LLM

import json
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

load_dotenv(Path(__file__).resolve().parent / ".env")

_local_str = str(os.getenv("USE_LOCAL_LLM", "true")).strip().strip('\'"').lower()
USE_LOCAL_LLM = _local_str in ["true", "1", "yes", "y"]

HF_MODEL_ID = os.getenv("HF_MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.2")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

_benchmark = "content-moderation-openenv"

if USE_LOCAL_LLM:
    print(f"Initializing Local Model: {HF_MODEL_ID} (Quantized if GPU)")
    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_ID)
    
    device_map = "auto" if torch.cuda.is_available() else "cpu"
    
    model_kwargs = {
        "device_map": device_map,
    }
    if torch.cuda.is_available():
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )
        model_kwargs["quantization_config"] = bnb_config
    else:
        model_kwargs["torch_dtype"] = torch.float32

    try:
        model = AutoModelForCausalLM.from_pretrained(HF_MODEL_ID, **model_kwargs)
        print("Local model loaded successfully.")
    except Exception as e:
        print(f"Failed to load local model: {e}")
        sys.exit(1)
    
    client = None
else:
    print(f"Initializing Cloud OpenAI Model: {MODEL_NAME}")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        sys.exit("ERROR: Set OPENAI_API_KEY environment variable")
    client = OpenAI(api_key=OPENAI_API_KEY)

VALID_DECISIONS = {"approve", "remove", "escalate"}
VALID_REASON_CODES = {
    "hate_speech", "harassment", "spam", "misinformation",
    "self_harm", "violence", "sexual_content", "clean",
}
VALID_SEVERITIES = {"low", "medium", "high"}

# map LLM outputs to valid reason codes
# (built up over testing — LLMs get creative with labels)
REASON_CODE_MAP = {
    "abuse": "harassment", "insult": "harassment", "toxic": "harassment",
    "offensive": "harassment", "bullying": "harassment", "profanity": "harassment",
    "sarcasm": "harassment", "mocking": "harassment", "aggressive": "harassment",
    "mild_abuse": "harassment", "condescending": "harassment",
    "harsh_criticism": "harassment", "borderline_abuse": "harassment",
    "mixed_tone": "harassment", "harmful": "harassment",
    "inappropriate": "harassment", "toxicity": "harassment",
    "sarcasm_obfuscated": "harassment", "obfuscated_sarcasm": "harassment",
    "obfuscated_abuse": "harassment",
    "threat": "violence", "threats": "violence",
    "violent_abuse": "violence", "dangerous": "violence",
    "scam": "spam", "phishing": "spam", "fraud": "spam",
    "explicit": "sexual_content", "nsfw": "sexual_content",
    "nsfw_spam": "sexual_content",
    "false_information": "misinformation", "disinformation": "misinformation",
    "suicide": "self_harm", "self-harm": "self_harm", "selfharm": "self_harm",
    "hate_generalization": "hate_speech",
    "safe": "clean", "none": "clean", "no_violation": "clean",
    "criticism": "clean", "advice": "clean", "neutral_feedback": "clean",
    "balanced_feedback": "clean", "safe_content": "clean",
}

DECISION_MAP = {
    "allow": "approve", "flag": "escalate", "flag_for_review": "escalate",
    "review": "escalate", "block": "remove", "delete": "remove",
    "reject": "remove", "ban": "remove",
}

SYSTEM_PROMPT = """You classify social media posts for content moderation. Output valid JSON only — no markdown, no extra text.

Format:
{"decision":"<approve|remove|escalate>","reason_code":"<hate_speech|harassment|spam|misinformation|self_harm|violence|sexual_content|clean>","severity":"<low|medium|high>","confidence":<0.0-1.0>,"explanation":"<brief reason, under 10 words>"}

Guidelines:
- spam, scams, promo → remove (spam)
- direct insults, personal attacks → remove (harassment)
- hate targeting groups → remove (hate_speech)
- threats → remove (violence)
- self-harm encouragement → remove (self_harm)
- explicit/sexual → remove (sexual_content)
- misinfo, false claims → remove (misinformation)
- sarcasm, mocking, passive-aggressive → escalate (harassment)
- borderline rude, dismissive → escalate (harassment)
- obfuscated stuff (l33t, symbols) → read through it, classify the intent
- safe, constructive → approve (clean)

When in doubt, escalate. Don't approve anything borderline.
Words like "dumb", "trash", "stupid" aimed at a person → escalate at minimum.

Severity: low = minor, medium = borderline toxic, high = clearly harmful.

Always output JSON. No commentary."""


def _extract_json(text):
    """Try to pull JSON from whatever the LLM spat out."""
    if not text:
        return None
    text = text.strip()

    # strip markdown fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # sometimes the LLM doesn't close its braces
    if text.count("{") > text.count("}"):
        text += "}" * (text.count("{") - text.count("}"))
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # grab first {...} block
    for m in re.findall(r"\{[^{}]*\}", text, re.DOTALL):
        try:
            return json.loads(m)
        except (json.JSONDecodeError, ValueError):
            continue

    # last resort: greedy match
    for m in re.findall(r"\{.*\}", text, re.DOTALL):
        try:
            return json.loads(m)
        except (json.JSONDecodeError, ValueError):
            continue

    return None


def _sanitize_action(raw):
    """Normalize fields to valid enums, fill in defaults for anything missing."""

    decision = str(raw.get("decision", "escalate")).strip().lower()
    if decision not in VALID_DECISIONS:
        decision = DECISION_MAP.get(decision, "escalate")
    if decision not in VALID_DECISIONS:
        decision = "escalate"

    reason = str(raw.get("reason_code", "harassment")).strip().lower()
    reason = reason.replace(" ", "_").replace("-", "_")
    if reason not in VALID_REASON_CODES:
        reason = REASON_CODE_MAP.get(reason, "harassment")
    if reason not in VALID_REASON_CODES:
        reason = "harassment"

    severity = str(raw.get("severity", "medium")).strip().lower()
    if severity not in VALID_SEVERITIES:
        severity = "medium"

    try:
        confidence = float(raw.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.5

    explanation = str(raw.get("explanation", "flagged for review"))
    if not explanation or explanation == "None":
        explanation = "flagged for review"
    if len(explanation) > 200:
        explanation = explanation[:197] + "..."

    return {
        "decision": decision,
        "reason_code": reason,
        "severity": severity,
        "confidence": round(confidence, 2),
        "explanation": explanation,
    }


FALLBACK_ACTION = {
    "decision": "escalate",
    "reason_code": "harassment",
    "severity": "medium",
    "confidence": 0.3,
    "explanation": "LLM didn't return usable JSON",
}


def _call_llm(prompt):
    """Call model with retries. Always returns a valid action dict."""
    if USE_LOCAL_LLM:
        try:
            full_prompt = f"[INST] {SYSTEM_PROMPT}\n\n{prompt} [/INST]"
            inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
            
            outputs = model.generate(
                **inputs,
                max_new_tokens=120,
                do_sample=False
            )
            
            new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
            raw_text = tokenizer.decode(new_tokens, skip_special_tokens=True)
            
            if not raw_text or not raw_text.strip():
                return FALLBACK_ACTION.copy()
                
            parsed = _extract_json(raw_text)
            if parsed and isinstance(parsed, dict):
                return _sanitize_action(parsed)
        except Exception as e:
            print(f"[_call_llm] Local Model Error: {e}")
            
        return FALLBACK_ACTION.copy()

    for attempt in range(5):
        backoff = min(2 ** attempt, 16)
        try:
            # HACK: gemma chokes on system messages
            if "gemma" in MODEL_NAME.lower():
                messages = [{"role": "user", "content": SYSTEM_PROMPT + "\n\n" + prompt}]
            else:
                messages = [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]

            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.0,
                max_tokens=120,
            )
            raw_text = resp.choices[0].message.content

            if not raw_text or not raw_text.strip():
                time.sleep(backoff)
                continue

            parsed = _extract_json(raw_text)
            if parsed and isinstance(parsed, dict):
                return _sanitize_action(parsed)

            time.sleep(backoff)
        except Exception:
            time.sleep(backoff)

    return FALLBACK_ACTION.copy()


def _action_str(action):
    return json.dumps(action, separators=(",", ":"))


def run_task(task_id, env_url):
    """Run a task end-to-end, logging in the validator format."""
    rewards = []
    step_num = 0

    model_id_str = HF_MODEL_ID if USE_LOCAL_LLM else MODEL_NAME
    print(f"[START] task={task_id} env={_benchmark} model={model_id_str}")

    try:
        r = requests.post(f"{env_url}/reset", params={"task_id": task_id}, timeout=30)
        r.raise_for_status()
        obs = r.json()
    except Exception as e:
        print(f"[STEP] step=1 action=null reward=0.01 done=true error={e}")
        print(f"[END] success=false steps=0 score=0.001")
        return False, 0, []

    if "error" in obs:
        print(f"[STEP] step=1 action=null reward=0.01 done=true error={obs['error']}")
        print(f"[END] success=false steps=0 score=0.001")
        return False, 0, []

    while step_num < 50:
        post = obs.get("post", {})
        author = obs.get("author", {})
        thread = obs.get("thread_context", {})

        prompt = (
            f"Classify this social media post for content moderation.\n\n"
            f"Task Instructions: {obs.get('instructions', '')}\n\n"
            f"Post Content: {post.get('content', '')}\n\n"
            f"Author Context:\n"
            f"- Account age: {author.get('account_age_days', 0)} days\n"
            f"- Prior violations: {author.get('prior_violations', 0)}\n"
            f"- Total posts: {author.get('total_posts', 0)}\n\n"
            f"Thread Topic: {thread.get('topic', 'general')}\n\n"
            f"Respond with ONLY the JSON classification."
        )

        action = _call_llm(prompt)
        step_num += 1

        try:
            r = requests.post(f"{env_url}/step", json=action, timeout=30)
            r.raise_for_status()
            result = r.json()
        except Exception as e:
            print(f"[STEP] step={step_num} action={_action_str(action)} reward=0.01 done=true error={e}")
            rewards.append(0.01)
            break

        if "error" in result:
            print(f"[STEP] step={step_num} action={_action_str(action)} reward=0.01 done=true error={result['error']}")
            rewards.append(0.01)
            break

        reward_val = result.get("reward", {}).get("value", 0.01)
        reward_val = min(0.999, max(0.001, float(reward_val)))
        done = result.get("done", False)
        rewards.append(reward_val)

        print(f"[STEP] step={step_num} action={_action_str(action)} reward={reward_val:.4f} done={str(done).lower()} error=null")

        if done:
            break
        obs = result.get("observation", obs)

    if rewards:
        final_score = sum(rewards) / len(rewards)
    else:
        final_score = 0.5
    final_score = min(0.999, max(0.001, final_score))
    print(f"[END] success=true steps={step_num} score={final_score:.4f}")
    return True, step_num, rewards


if __name__ == "__main__":
    env_base = os.getenv("OPENENV_URL", "http://127.0.0.1:7860")

    for task_id in ["task1", "task2", "task3"]:
        try:
            run_task(task_id, env_base)
        except Exception as e:
            model_id_str = HF_MODEL_ID if USE_LOCAL_LLM else MODEL_NAME
            print(f"[START] task={task_id} env={_benchmark} model={model_id_str}")
            print(f"[STEP] step=1 action=null reward=0.01 done=true error={e}")
            print(f"[END] success=false steps=0 score=0.001")
