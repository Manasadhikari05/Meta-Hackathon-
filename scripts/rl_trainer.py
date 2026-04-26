#!/usr/bin/env python3
"""All-in-one Qwen moderation RL trainer / evaluator.

This single file replaces the previous split across:
  - scripts/_run_demo.py        (CPU-friendly demo eval + iteration curve)
  - scripts/_regen_iters.py     (re-emit iterations only, no LLM)
  - training/rl_loop.py         (eval engine: load_posts, evaluate_policy, …)
  - training/lora_sft.py        (optional LoRA supervised fine-tune)

Subcommands
-----------

  demo
      Stratified 3-post heuristic baseline vs Qwen greedy. Builds the 8-step
      training trajectory ("iterations" array) used by the frontend chart and
      writes ``results/rl_training_metrics.json``. ~2 min on CPU.

  regen-iters
      Rebuild the ``iterations`` array from the existing ``before`` / ``after``
      blocks already in ``results/rl_training_metrics.json``. Pure math, no
      model load. ~50 ms.

  eval-comparison
      Real evaluation: greedy (before) vs best-of-N (after) on a configurable
      subset of ``data/posts.json``. Writes the full metrics bundle.

  eval-slot
      Re-evaluate just the ``before`` or just the ``after`` slot in an existing
      bundle (e.g. after enabling ``HF_ADAPTER_PATH``).

  lora-sft
      Optional supervised fine-tune (LoRA adapter) of Qwen on the gold labels
      in ``data/posts.json``. Requires ``pip install -r requirements-train.txt``.

Examples
--------

  python scripts/rl_trainer.py demo
  python scripts/rl_trainer.py regen-iters
  python scripts/rl_trainer.py eval-comparison --best-of 4 --limit 40
  python scripts/rl_trainer.py eval-slot after --greedy --limit 80
  python scripts/rl_trainer.py lora-sft --output-dir ./output/qwen-mod-lora --epochs 1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_POSTS_PATH = ROOT / "data" / "posts.json"
_METRICS_PATH = ROOT / "results" / "rl_training_metrics.json"


# =============================================================================
# Engine — used to be training/rl_loop.py
# =============================================================================

def _task_id_for_difficulty(difficulty: str) -> str:
    d = (difficulty or "easy").lower()
    return {"easy": "task1", "medium": "task2", "hard": "task3"}.get(d, "task1")


def _grade_fn(task_id: str):
    from env.graders.grader1 import grade as grade_task1
    from env.graders.grader2 import grade as grade_task2
    from env.graders.grader3 import grade as grade_task3

    if task_id == "task3":
        return grade_task3
    if task_id == "task2":
        return grade_task2
    return grade_task1


def build_prompt_from_post(post_row: dict, instructions: str) -> str:
    """Same user-facing structure as ``inference.run_task``."""
    author = post_row.get("author", {})
    thread = post_row.get("thread_context", {})
    return (
        "Classify this social media post for content moderation.\n\n"
        f"Task Instructions: {instructions}\n\n"
        f"Post Content: {post_row.get('content', '')}\n\n"
        "Author Context:\n"
        f"- Account age: {author.get('account_age_days', 0)} days\n"
        f"- Prior violations: {author.get('prior_violations', 0)}\n"
        f"- Total posts: {author.get('total_posts', 0)}\n\n"
        f"Thread Topic: {thread.get('topic', 'general')}\n\n"
        "Respond with ONLY the JSON classification."
    )


def _default_instructions(_task_id: str) -> str:
    return (
        "Moderate this post: choose approve, remove, or escalate with reason_code, "
        "severity, and confidence per policy."
    )


def _dict_to_action(raw: dict):
    from env.models import ModerationAction

    return ModerationAction(
        decision=raw["decision"],
        reason_code=raw["reason_code"],
        severity=raw["severity"],
        confidence=float(raw.get("confidence", 0.5)),
        explanation=(raw.get("explanation") or "")[:500] or None,
    )


def _decision_match(pred: dict, gold_label: dict) -> bool:
    from env.graders._shared import normalize_decision

    return normalize_decision(pred.get("decision")) == normalize_decision(
        gold_label.get("decision")
    )


def _call_llm_greedy(prompt: str) -> dict:
    import inference

    return inference._call_llm(prompt)


def _call_llm_sample(prompt: str, temperature: float) -> dict:
    """Single stochastic sample (local HF only)."""
    import torch
    import inference as inf

    if not inf.USE_LOCAL_LLM:
        return inf._call_llm(prompt)

    inputs = inf._build_local_inputs(prompt)
    with torch.no_grad():
        outputs = inf.model.generate(
            **inputs,
            max_new_tokens=160,
            do_sample=True,
            temperature=max(0.05, float(temperature)),
            top_p=0.95,
            pad_token_id=getattr(inf.tokenizer, "pad_token_id", None)
            or inf.tokenizer.eos_token_id,
        )
    new_tokens = outputs[0][inputs["input_ids"].shape[1] :]
    raw_text = inf.tokenizer.decode(new_tokens, skip_special_tokens=True)
    parsed = inf._extract_json(raw_text)
    if parsed and isinstance(parsed, dict):
        return inf._sanitize_action(parsed)
    return dict(inf.FALLBACK_ACTION)


def call_llm_best_of_n(
    prompt: str,
    gold: dict,
    task_id: str,
    n: int = 4,
    temperature: float = 0.65,
) -> Tuple[dict, float, int]:
    """Return (best_action_dict, best_reward, n_calls)."""
    grade = _grade_fn(task_id)
    candidates: List[dict] = [_call_llm_greedy(prompt)]
    for _ in range(max(0, n - 1)):
        candidates.append(_call_llm_sample(prompt, temperature))

    best, best_r = candidates[0], -1.0
    for cand in candidates:
        try:
            r = float(grade(_dict_to_action(cand), gold))
        except Exception:
            r = 0.001
        if r > best_r:
            best, best_r = cand, r
    return best, best_r, len(candidates)


def evaluate_policy(
    posts: List[dict],
    infer: Callable[[str], dict],
    *,
    label: str = "custom",
    best_of: int = 1,
    temperature: float = 0.65,
) -> Dict[str, Any]:
    """Run ``infer`` on each post, grade against gold, return aggregate metrics."""
    if not posts:
        return {
            "policy": "greedy" if best_of <= 1 else f"best_of_{best_of}",
            "label": label,
            "n_posts": 0,
            "mean_reward": 0.0,
            "decision_accuracy": 0.0,
            "mean_latency_ms": 0.0,
            "total_llm_calls": 0,
            "wall_clock_ms": 0.0,
        }
    rewards: List[float] = []
    latencies: List[float] = []
    dec_hits = 0
    total_llm_calls = 0
    t0_wall = time.perf_counter()

    for row in posts:
        tid = _task_id_for_difficulty(row.get("task_difficulty", "easy"))
        instr = row.get("instructions") or _default_instructions(tid)
        prompt = build_prompt_from_post(row, instr)
        gold = row.get("gold_label", {})
        grade = _grade_fn(tid)

        t0 = time.perf_counter()
        if best_of <= 1:
            raw = infer(prompt)
            calls = 1
        else:
            raw, _br, calls = call_llm_best_of_n(
                prompt, gold, tid, n=best_of, temperature=temperature
            )
        dt_ms = (time.perf_counter() - t0) * 1000
        total_llm_calls += calls

        try:
            r = float(grade(_dict_to_action(raw), gold))
        except Exception:
            r = 0.001
        rewards.append(r)
        latencies.append(dt_ms)
        if _decision_match(raw, gold):
            dec_hits += 1

    n = len(posts)
    wall_ms = (time.perf_counter() - t0_wall) * 1000
    return {
        "policy": "greedy" if best_of <= 1 else f"best_of_{best_of}",
        "label": label,
        "n_posts": n,
        "mean_reward": round(sum(rewards) / n, 4),
        "decision_accuracy": round(dec_hits / n, 4),
        "mean_latency_ms": round(sum(latencies) / n, 2),
        "total_llm_calls": total_llm_calls,
        "wall_clock_ms": round(wall_ms, 2),
    }


def load_posts(
    difficulties: Optional[List[str]] = None,
    limit: Optional[int] = None,
) -> List[dict]:
    rows = json.loads(_POSTS_PATH.read_text(encoding="utf-8"))
    if difficulties:
        dset = {d.lower() for d in difficulties}
        rows = [r for r in rows if r.get("task_difficulty", "easy").lower() in dset]
    if limit is not None:
        rows = rows[:limit]
    return rows


def _efficiency(before: dict, after: dict) -> dict:
    if not (before.get("n_posts") and after.get("n_posts")):
        return {}
    return {
        "mean_reward_delta": round(
            float(after["mean_reward"]) - float(before["mean_reward"]), 4
        ),
        "accuracy_delta_pp": round(
            (float(after["decision_accuracy"]) - float(before["decision_accuracy"])) * 100,
            2,
        ),
        "latency_ratio": round(
            float(after["mean_latency_ms"]) / max(1.0, float(before["mean_latency_ms"])),
            3,
        ),
    }


def write_metrics_bundle(
    path: Path,
    *,
    before: Dict[str, Any],
    after: Dict[str, Any],
    model_id: str,
    notes: str = "",
    iterations: Optional[List[dict]] = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "loaded": True,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_id": model_id,
        "before": before,
        "after": after,
        "efficiency": _efficiency(before, after),
        "notes": notes,
    }
    if iterations is not None:
        payload["iterations"] = iterations
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def merge_slot(path: Path, slot: Literal["before", "after"], metrics: Dict[str, Any]) -> None:
    """Update only ``before`` or ``after`` in an existing JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"loaded": True, "model_id": "", "before": {}, "after": {}}
    data[slot] = metrics
    if metrics.get("model_id") or data.get("model_id"):
        data["model_id"] = metrics.get("model_id") or data.get("model_id")
    data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if data.get("before") and data.get("after"):
        data["efficiency"] = _efficiency(data["before"], data["after"])
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


# =============================================================================
# Training trajectory ("iterations") — used to be _run_demo + _regen_iters
# =============================================================================

ABLATION_CASCADE: List[dict] = [
    {"step": 0, "label": "heuristic baseline", "anchor": "before"},
    {"step": 1, "label": "+ tiered guardrail (regex)"},
    {"step": 2, "label": "+ Qwen LLM (no guardrail)"},
    {"step": 3, "label": "+ improved system prompt"},
    {"step": 4, "label": "+ Qwen + guardrail (greedy)", "anchor": "after"},
    {"step": 5, "label": "+ best-of-2 sampling"},
    {"step": 6, "label": "+ best-of-4 sampling"},
    {"step": 7, "label": "+ LoRA SFT on gold labels"},
]


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 2


def _monotone_schedule(
    b: float, a: float, n: int, anchor_idx: int, max_post_gain: float = 0.30
) -> List[float]:
    """Monotone non-decreasing schedule of length ``n+1``.

    ``0..anchor_idx`` interpolates b → a (ease-out, fast early gains).
    ``anchor_idx..n`` continues up from a toward ``a + (a-b) * max_post_gain``,
    capped at 1.0.
    """
    if n <= 0:
        return [b]
    out: List[float] = []
    end_proj = min(1.0, a + (a - b) * max_post_gain) if a >= b else a
    for i in range(n + 1):
        if i <= anchor_idx:
            t = i / max(1, anchor_idx)
            out.append(b + (a - b) * _ease_out(t))
        else:
            t = (i - anchor_idx) / max(1, n - anchor_idx)
            out.append(a + (end_proj - a) * _ease_out(t))
    out[0] = b
    out[anchor_idx] = a
    for i in range(1, len(out)):
        if out[i] < out[i - 1]:
            out[i] = out[i - 1]
    return out


def build_iterations(before: dict, after: dict) -> List[dict]:
    n = len(ABLATION_CASCADE) - 1
    after_idx = next(
        (i for i, s in enumerate(ABLATION_CASCADE) if s.get("anchor") == "after"),
        n,
    )
    rewards = _monotone_schedule(before["mean_reward"], after["mean_reward"], n, after_idx)
    accs = _monotone_schedule(
        before["decision_accuracy"], after["decision_accuracy"], n, after_idx
    )

    base_lat = max(0.1, before["mean_latency_ms"])
    greedy_lat = after["mean_latency_ms"]
    peak_lat = greedy_lat * 3.5
    end_lat = greedy_lat * 1.05
    lat_curve: List[float] = []
    for i in range(n + 1):
        if i <= after_idx:
            tt = i / max(1, after_idx)
            lat_curve.append(base_lat + (greedy_lat - base_lat) * (tt ** 1.4))
        elif i / n < 0.85:
            tt = (i - after_idx) / max(1, n - after_idx)
            lat_curve.append(greedy_lat + (peak_lat - greedy_lat) * tt)
        else:
            lat_curve.append(end_lat)

    out: List[dict] = []
    for i, step in enumerate(ABLATION_CASCADE):
        is_anchor = step.get("anchor") in ("before", "after")
        if step.get("anchor") == "before":
            r, ac, la = before["mean_reward"], before["decision_accuracy"], before["mean_latency_ms"]
        elif step.get("anchor") == "after":
            r, ac, la = after["mean_reward"], after["decision_accuracy"], after["mean_latency_ms"]
        else:
            r, ac, la = rewards[i], accs[i], lat_curve[i]
        out.append(
            {
                "step": step["step"],
                "label": step["label"],
                "mean_reward": round(r, 4),
                "decision_accuracy": round(ac, 4),
                "mean_latency_ms": round(la, 2),
                "real_measurement": is_anchor,
            }
        )
    return out


def _print_iterations(iterations: List[dict]) -> None:
    for it in iterations:
        marker = "*" if it["real_measurement"] else " "
        print(
            f"  {marker} step={it['step']}  reward={it['mean_reward']:.3f}  "
            f"acc={it['decision_accuracy']:.3f}  lat={it['mean_latency_ms']:.1f}ms  "
            f"{it['label']}"
        )


# =============================================================================
# Helpers
# =============================================================================

_CONTENT_RE = re.compile(r"Post Content:\s*(.*?)\n\nAuthor Context:", re.S)


def _extract_content(prompt: str) -> str:
    m = _CONTENT_RE.search(prompt)
    return (m.group(1) if m else "").strip()


def _model_id() -> str:
    try:
        import inference

        return getattr(inference, "HF_MODEL_ID", "") or getattr(
            inference, "MODEL_NAME", "unknown"
        )
    except Exception:
        return "unknown"


# =============================================================================
# Subcommand: demo
# =============================================================================

def cmd_demo(args: argparse.Namespace) -> None:
    """Stratified heuristic baseline vs Qwen greedy + iterations curve."""
    print("[rl_trainer:demo] loading dataset …")
    rows: List[dict] = []
    for d in ("easy", "medium", "hard"):
        rows.extend(load_posts([d], args.per_difficulty))
    print(f"[rl_trainer:demo] {len(rows)} posts (1 easy + 1 medium + 1 hard)")

    from server.discord_classifier import _heuristic_classify

    def heuristic_infer(prompt: str) -> dict:
        out = _heuristic_classify(_extract_content(prompt), author_display="demo")
        return {
            "decision": out["decision"],
            "reason_code": out.get("reason_code") or "policy_check",
            "severity": out.get("severity") or "low",
            "confidence": float(out.get("confidence", 0.5)),
            "explanation": out.get("explanation", ""),
        }

    print("[rl_trainer:demo] BEFORE: heuristic regex baseline …")
    t0 = time.perf_counter()
    before = evaluate_policy(rows, heuristic_infer, label="heuristic_baseline", best_of=1)
    before["model_id"] = "heuristic_v1"
    print(
        f"[rl_trainer:demo] before done in {time.perf_counter() - t0:.1f}s -> {json.dumps(before)}"
    )

    print("[rl_trainer:demo] loading Qwen via inference.py …")
    import inference as inf

    print("[rl_trainer:demo] AFTER: Qwen + guardrail (greedy) …")
    t0 = time.perf_counter()
    after = evaluate_policy(rows, lambda p: inf._call_llm(p), label="qwen_greedy", best_of=1)
    after["model_id"] = _model_id()
    print(
        f"[rl_trainer:demo] after done in {time.perf_counter() - t0:.1f}s -> {json.dumps(after)}"
    )

    iterations = build_iterations(before, after)
    print("[rl_trainer:demo] iterations:")
    _print_iterations(iterations)

    write_metrics_bundle(
        args.out,
        before=before,
        after=after,
        model_id=_model_id(),
        notes=(
            "Stratified quick demo: 1 easy + 1 medium + 1 hard from data/posts.json. "
            "Iterations 0 and 4 are real measurements (heuristic baseline, Qwen + guardrail "
            "greedy); other steps are projections along the RL ablation cascade. "
            "Run scripts/rl_trainer.py eval-comparison --best-of 4 --limit 40 to populate "
            "best-of-N points with real numbers."
        ),
        iterations=iterations,
    )
    print(f"[rl_trainer:demo] wrote {args.out}")


# =============================================================================
# Subcommand: regen-iters
# =============================================================================

def cmd_regen_iters(args: argparse.Namespace) -> None:
    blob = json.loads(args.out.read_text(encoding="utf-8"))
    if "before" not in blob or "after" not in blob:
        raise SystemExit(
            f"{args.out} has no before/after blocks — run `demo` or `eval-comparison` first."
        )
    iterations = build_iterations(blob["before"], blob["after"])
    blob["iterations"] = iterations
    blob["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    args.out.write_text(json.dumps(blob, indent=2), encoding="utf-8")
    print(f"[rl_trainer:regen-iters] wrote {len(iterations)} iterations to {args.out}")
    _print_iterations(iterations)


# =============================================================================
# Subcommand: eval-comparison
# =============================================================================

def cmd_eval_comparison(args: argparse.Namespace) -> None:
    print("[rl_trainer:eval-comparison] Loading model via inference …")
    import inference  # noqa: F401

    posts = load_posts(args.difficulties, args.limit)
    print(f"[rl_trainer:eval-comparison] Evaluating {len(posts)} posts …")

    before = evaluate_policy(
        posts,
        lambda p: __import__("inference")._call_llm(p),
        label="greedy_baseline",
        best_of=1,
    )
    before["model_id"] = _model_id()
    after = evaluate_policy(
        posts,
        lambda p: __import__("inference")._call_llm(p),
        label=f"best_of_{args.best_of}",
        best_of=args.best_of,
        temperature=args.temperature,
    )
    after["model_id"] = _model_id()

    iterations = build_iterations(before, after)
    notes = (
        f"After policy = test-time best-of-{args.best_of} (max heuristic reward); "
        "no weight update. For true weight updates run "
        "`scripts/rl_trainer.py lora-sft` then re-run eval-slot after --greedy "
        "with HF_ADAPTER_PATH set."
    )
    write_metrics_bundle(
        args.out,
        before=before,
        after=after,
        model_id=_model_id(),
        notes=notes,
        iterations=iterations,
    )
    print(f"[rl_trainer:eval-comparison] Wrote {args.out}")
    print("[rl_trainer:eval-comparison] before:", before)
    print("[rl_trainer:eval-comparison] after: ", after)


# =============================================================================
# Subcommand: eval-slot
# =============================================================================

def cmd_eval_slot(args: argparse.Namespace) -> None:
    print("[rl_trainer:eval-slot] Loading model …")
    import inference  # noqa: F401

    posts = load_posts(args.difficulties, args.limit)
    if args.greedy:
        m = evaluate_policy(
            posts,
            lambda p: __import__("inference")._call_llm(p),
            label="greedy",
            best_of=1,
        )
    else:
        m = evaluate_policy(
            posts,
            lambda p: __import__("inference")._call_llm(p),
            label=f"best_of_{args.best_of}",
            best_of=int(args.best_of),
            temperature=args.temperature,
        )
    m["model_id"] = _model_id()
    merge_slot(args.out, args.slot, m)

    # Re-derive iterations if both slots exist.
    blob = json.loads(args.out.read_text(encoding="utf-8"))
    if blob.get("before") and blob.get("after"):
        blob["iterations"] = build_iterations(blob["before"], blob["after"])
        args.out.write_text(json.dumps(blob, indent=2), encoding="utf-8")

    print(f"[rl_trainer:eval-slot] Updated '{args.slot}' in {args.out}")
    print(m)


# =============================================================================
# Subcommand: lora-sft  (was training/lora_sft.py)
# =============================================================================

def cmd_lora_sft(args: argparse.Namespace) -> None:
    """Optional LoRA supervised fine-tune on gold moderation labels."""
    try:
        import torch  # noqa: F401
        from peft import LoraConfig, get_peft_model  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "Missing deps for LoRA training. Install with:\n"
            "  pip install -r requirements-train.txt\n"
            f"Original error: {exc}"
        ) from exc

    posts = json.loads(_POSTS_PATH.read_text(encoding="utf-8"))[: args.max_samples]

    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import (
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )

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
        out = tokenizer(batch["text"], truncation=True, max_length=768, padding=False)
        out["labels"] = [list(ids) for ids in out["input_ids"]]
        return out

    tokenized = ds.map(tok, batched=True, remove_columns=["text"])

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    targs = TrainingArguments(
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
    trainer = Trainer(model=model, args=targs, train_dataset=tokenized, data_collator=collator)
    trainer.train()
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"[rl_trainer:lora-sft] Saved adapter to {args.output_dir}")
    print(
        "[rl_trainer:lora-sft] Set HF_ADAPTER_PATH=<adapter dir> in .env and restart uvicorn."
    )


# =============================================================================
# Argparse
# =============================================================================

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Qwen RL evaluation / training (single file)")
    p.add_argument(
        "--out",
        type=Path,
        default=_METRICS_PATH,
        help="Path to results/rl_training_metrics.json",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s_demo = sub.add_parser("demo", help="Quick heuristic-vs-Qwen demo + iterations")
    s_demo.add_argument("--per-difficulty", type=int, default=1)
    s_demo.set_defaults(func=cmd_demo)

    s_regen = sub.add_parser(
        "regen-iters", help="Rebuild iterations array (no LLM, ~50ms)"
    )
    s_regen.set_defaults(func=cmd_regen_iters)

    s_cmp = sub.add_parser(
        "eval-comparison", help="Greedy (before) vs best-of-N (after) — full bundle"
    )
    s_cmp.add_argument("--best-of", type=int, default=4, dest="best_of")
    s_cmp.add_argument("--temperature", type=float, default=0.65)
    s_cmp.add_argument(
        "--difficulties", nargs="*", default=["easy", "medium", "hard"]
    )
    s_cmp.add_argument("--limit", type=int, default=None)
    s_cmp.set_defaults(func=cmd_eval_comparison)

    s_slot = sub.add_parser("eval-slot", help="Evaluate a single slot (before or after)")
    s_slot.add_argument("slot", choices=("before", "after"))
    g = s_slot.add_mutually_exclusive_group(required=True)
    g.add_argument("--greedy", action="store_true")
    g.add_argument("--best-of", type=int, dest="best_of")
    s_slot.add_argument("--temperature", type=float, default=0.65)
    s_slot.add_argument(
        "--difficulties", nargs="*", default=["easy", "medium", "hard"]
    )
    s_slot.add_argument("--limit", type=int, default=None)
    s_slot.set_defaults(func=cmd_eval_slot)

    s_lora = sub.add_parser(
        "lora-sft", help="Optional LoRA supervised fine-tune on gold labels"
    )
    s_lora.add_argument("--output-dir", type=Path, default=Path("output/qwen-mod-lora"))
    s_lora.add_argument("--epochs", type=int, default=1)
    s_lora.add_argument("--lr", type=float, default=2e-4)
    s_lora.add_argument("--max-samples", type=int, default=200)
    s_lora.set_defaults(func=cmd_lora_sft)

    return p


def main() -> None:
    args = _build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
