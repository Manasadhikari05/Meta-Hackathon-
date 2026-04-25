# Minimal HF TRL training script for ContentModerationEnv
# Intended for Colab demo verification in hackathon judging.

import requests
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

BASE_URL = "http://127.0.0.1:7860"
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"


def collect_rows(task_id: str = "task2", max_steps: int = 8) -> list[dict]:
    rows: list[dict] = []
    obs = requests.post(f"{BASE_URL}/reset", params={"task_id": task_id}, timeout=30).json()

    for _ in range(max_steps):
        prompt = (
            "You are a moderation model. Return JSON with decision, reason_code, "
            "severity, confidence, explanation.\n\n"
            f"Post: {obs['post']['content']}\n"
            f"Author violations: {obs['author']['prior_violations']}\n"
            f"Topic: {obs['thread_context']['topic']}"
        )
        target = (
            '{"decision":"escalate","reason_code":"harassment","severity":"medium",'
            '"confidence":0.6,"explanation":"borderline risk"}'
        )
        rows.append({"text": f"<|user|>\n{prompt}\n<|assistant|>\n{target}"})

        step = requests.post(
            f"{BASE_URL}/step",
            json={
                "decision": "escalate",
                "reason_code": "harassment",
                "severity": "medium",
                "confidence": 0.6,
                "explanation": "borderline risk",
            },
            timeout=30,
        ).json()
        if step["done"]:
            break
        obs = step["observation"]

    return rows


def main() -> None:
    train_ds = Dataset.from_list(collect_rows(task_id="task2", max_steps=8))
    print("Training rows:", len(train_ds))

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)

    cfg = SFTConfig(
        output_dir="trl-minimal-demo",
        per_device_train_batch_size=1,
        gradient_accumulation_steps=2,
        max_steps=20,
        learning_rate=2e-5,
        logging_steps=1,
        save_steps=20,
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
    print("Done: minimal TRL demo completed.")


if __name__ == "__main__":
    main()
