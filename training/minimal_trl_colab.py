"""
Judge-ready minimal TRL script for Colab.

What this script demonstrates:
1) Build a tiny supervised dataset from environment observations.
2) Train with HF TRL (SFTTrainer).
3) Compare baseline vs post-train policy rewards.
4) Save simple evidence plots for README/submit.
"""

from __future__ import annotations

import json
import os
import random
import re
from typing import Callable

import matplotlib.pyplot as plt
import requests
import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

BASE_URL = os.getenv("OPENENV_URL", "http://127.0.0.1:7860")
MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen2.5-0.5B-Instruct")
OUT_DIR = os.getenv("OUT_DIR", "trl-minimal-demo")
RANDOM_SEED = 7
random.seed(RANDOM_SEED)

VALID_DECISIONS = ["approve", "remove", "escalate"]
VALID_REASONS = [
    "hate_speech",
    "harassment",
    "spam",
    "misinformation",
    "self_harm",
    "violence",
    "sexual_content",
    "clean",
]
VALID_SEVERITIES = ["low", "medium", "high"]


def build_prompt(obs: dict) -> str:
    post = obs["post"]
    author = obs["author"]
    thread = obs["thread_context"]
    return (
        "Moderate the post and output JSON only with keys: "
        "decision, reason_code, severity, confidence, explanation.\n\n"
        f"Post: {post['content']}\n"
        f"Prior violations: {author['prior_violations']}\n"
        f"Topic: {thread['topic']}"
    )


def heuristic_teacher_action(post_text: str) -> dict:
    lower = post_text.lower()
    if any(k in lower for k in ["buy", "click", "free", "dm", "giveaway", "crypto"]):
        return {
            "decision": "remove",
            "reason_code": "spam",
            "severity": "high",
            "confidence": 0.92,
            "explanation": "likely promotional spam",
        }
    if any(k in lower for k in ["idiot", "dumb", "trash", "stupid", "hate"]):
        return {
            "decision": "remove",
            "reason_code": "harassment",
            "severity": "high",
            "confidence": 0.9,
            "explanation": "direct personal attack",
        }
    return {
        "decision": "approve",
        "reason_code": "clean",
        "severity": "low",
        "confidence": 0.8,
        "explanation": "safe content",
    }


def collect_rows(task_id: str = "task2", episodes: int = 4) -> list[dict]:
    rows: list[dict] = []
    for _ in range(episodes):
        obs = requests.post(f"{BASE_URL}/reset", params={"task_id": task_id}, timeout=30).json()
        while True:
            prompt = build_prompt(obs)
            target_action = heuristic_teacher_action(obs["post"]["content"])
            target_json = json.dumps(target_action, separators=(",", ":"))
            rows.append({"text": f"<|user|>\n{prompt}\n<|assistant|>\n{target_json}"})

            step = requests.post(f"{BASE_URL}/step", json=target_action, timeout=30).json()
            if step["done"]:
                break
            obs = step["observation"]
    return rows


def random_policy(_obs: dict) -> dict:
    return {
        "decision": random.choice(VALID_DECISIONS),
        "reason_code": random.choice(VALID_REASONS),
        "severity": random.choice(VALID_SEVERITIES),
        "confidence": 0.5,
        "explanation": "auto baseline",
    }


def parse_action(text: str) -> dict | None:
    candidates = re.findall(r"\{.*\}", text, flags=re.DOTALL)
    for chunk in candidates:
        try:
            data = json.loads(chunk)
            return {
                "decision": data.get("decision", "escalate"),
                "reason_code": data.get("reason_code", "harassment"),
                "severity": data.get("severity", "medium"),
                "confidence": float(data.get("confidence", 0.5)),
                "explanation": str(data.get("explanation", "auto prediction")),
            }
        except Exception:
            continue
    return None


def model_policy(model, tokenizer, obs: dict, device: str) -> dict:
    prompt = build_prompt(obs)
    inputs = tokenizer(f"<|user|>\n{prompt}\n<|assistant|>\n", return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=90, do_sample=False)
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    action = parse_action(text)
    return action if action else random_policy(obs)


def run_eval(policy_fn: Callable[[dict], dict], task_id: str = "task2", episodes: int = 3) -> float:
    rewards = []
    for _ in range(episodes):
        obs = requests.post(f"{BASE_URL}/reset", params={"task_id": task_id}, timeout=30).json()
        while True:
            action = policy_fn(obs)
            step = requests.post(f"{BASE_URL}/step", json=action, timeout=30).json()
            rewards.append(float(step["reward"]["value"]))
            if step["done"]:
                break
            obs = step["observation"]
    return sum(rewards) / max(1, len(rewards))


def save_plots(log_history: list[dict], baseline: float, trained: float) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

    losses = [x["loss"] for x in log_history if "loss" in x]
    steps = [x["step"] for x in log_history if "loss" in x]
    if losses and steps:
        plt.figure(figsize=(6, 4))
        plt.plot(steps, losses, marker="o")
        plt.title("Training Loss")
        plt.xlabel("Step")
        plt.ylabel("Loss")
        plt.grid(alpha=0.2)
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/loss_curve.png", dpi=150)
        plt.close()

    plt.figure(figsize=(5, 4))
    plt.bar(["baseline", "trained"], [baseline, trained])
    plt.title("Avg Reward: Before vs After")
    plt.ylabel("Reward")
    plt.ylim(0, 1)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/reward_before_after.png", dpi=150)
    plt.close()


def main() -> None:
    rows = collect_rows(task_id="task2", episodes=4)
    train_ds = Dataset.from_list(rows)
    print("Training rows:", len(train_ds))

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    baseline_reward = run_eval(random_policy, task_id="task2", episodes=3)
    print(f"Baseline avg reward: {baseline_reward:.4f}")

    cfg = SFTConfig(
        output_dir=OUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=2,
        max_steps=30,
        learning_rate=2e-5,
        logging_steps=1,
        save_steps=30,
        report_to=[],
    )
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_ds,
        dataset_text_field="text",
        args=cfg,
    )
    trainer.train()

    trained_reward = run_eval(lambda obs: model_policy(model, tokenizer, obs, device), task_id="task2", episodes=3)
    print(f"Trained avg reward:  {trained_reward:.4f}")

    save_plots(trainer.state.log_history, baseline_reward, trained_reward)
    print(f"Saved plots to: {OUT_DIR}/loss_curve.png and {OUT_DIR}/reward_before_after.png")


if __name__ == "__main__":
    main()
