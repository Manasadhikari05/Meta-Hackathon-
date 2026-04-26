"""Optional LoRA supervised fine-tuning on gold labels (behavior cloning).

This is **not** online RL (no PPO loop here); it distills the dataset’s gold
moderation labels into the base Qwen checkpoint using a small LoRA adapter.

Requirements (install separately if you train)::

    pip install peft accelerate datasets

Usage::

    python -m training.lora_sft --output-dir ./output/qwen-mod-lora --epochs 1

Then set ``HF_ADAPTER_PATH`` / ``./output/qwen-mod-lora`` in ``.env`` and
restart the API so ``inference.py`` merges the adapter.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    try:
        import torch  # noqa: F401
        from peft import LoraConfig, get_peft_model  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "Missing deps for LoRA training. Install with:\n"
            "  pip install peft accelerate datasets\n"
            f"Original error: {exc}"
        ) from exc

    p = argparse.ArgumentParser()
    p.add_argument("--output-dir", type=Path, default=Path("output/qwen-mod-lora"))
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--max-samples", type=int, default=200)
    args = p.parse_args()

    root = Path(__file__).resolve().parents[1]
    posts = json.loads((root / "data" / "posts.json").read_text(encoding="utf-8"))[
        : args.max_samples
    ]

    # Lazy imports after dependency check
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling

    import inference as inf

    tokenizer = inf.tokenizer
    model = inf.model

    lora = LoraConfig(
        r=8,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )
    model = get_peft_model(model, lora)

    def row_to_text(row: dict) -> str:
        from training.rl_loop import build_prompt_from_post, _default_instructions, _task_id_for_difficulty

        tid = _task_id_for_difficulty(row.get("task_difficulty", "easy"))
        g = row["gold_label"]
        raw_g = {
            "decision": {"allow": "approve", "remove": "remove", "escalate": "escalate"}.get(
                str(g.get("decision", "allow")).lower(), "approve"
            ),
            "reason_code": str(g.get("reason_code", "clean")).lower().replace("-", "_"),
            "severity": str(g.get("severity", "medium")).lower(),
            "confidence": 0.95,
            "explanation": (g.get("explanation") or "gold label")[:120],
        }
        target = json.dumps(inf._sanitize_action(raw_g), separators=(",", ":"))
        prompt = build_prompt_from_post(row, _default_instructions(tid))
        messages = [
            {"role": "system", "content": inf.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": target},
        ]
        if getattr(tokenizer, "chat_template", None):
            return tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=False
            )
        return f"[INST] {inf.SYSTEM_PROMPT}\n{prompt}\n[/INST]{target}"

    texts = [row_to_text(r) for r in posts]
    ds = Dataset.from_dict({"text": texts})

    def tok(batch):
        out = tokenizer(
            batch["text"],
            truncation=True,
            max_length=768,
            padding=False,
        )
        out["labels"] = [list(ids) for ids in out["input_ids"]]
        return out

    tokenized = ds.map(tok, batched=True, remove_columns=["text"])

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    args_out = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        learning_rate=args.lr,
        logging_steps=5,
        save_steps=200,
        save_total_limit=1,
        report_to="none",
    )
    trainer = Trainer(
        model=model,
        args=args_out,
        train_dataset=tokenized,
        data_collator=collator,
    )
    trainer.train()
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"[lora_sft] Saved adapter to {args.output_dir}")
    print("[lora_sft] Set HF_ADAPTER_PATH to this directory in .env and restart uvicorn.")


if __name__ == "__main__":
    main()
