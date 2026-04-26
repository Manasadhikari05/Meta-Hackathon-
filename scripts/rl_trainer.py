#!/usr/bin/env python3
"""CLI for Qwen moderation RL-style evaluation and metrics export.

Examples
--------
Greedy baseline + best-of-4 comparison (writes ``results/rl_training_metrics.json``)::

    python scripts/rl_trainer.py eval-comparison --best-of 4 --limit 30

After LoRA fine-tune (``HF_ADAPTER_PATH`` set), re-score *after* slot only::

    python scripts/rl_trainer.py eval-slot after --greedy --limit 80 \\
        --out results/rl_training_metrics.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _model_id() -> str:
    try:
        import inference

        return getattr(inference, "HF_MODEL_ID", "") or getattr(
            inference, "MODEL_NAME", "unknown"
        )
    except Exception:
        return "unknown"


def main() -> None:
    p = argparse.ArgumentParser(description="Qwen RL evaluation / metrics")
    p.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "rl_training_metrics.json",
        help="Output metrics JSON path",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    c1 = sub.add_parser(
        "eval-comparison",
        help="Run greedy (before) vs best-of-N (after) and write full bundle",
    )
    c1.add_argument("--best-of", type=int, default=4, dest="best_of")
    c1.add_argument("--temperature", type=float, default=0.65)
    c1.add_argument(
        "--difficulties",
        nargs="*",
        default=["easy", "medium", "hard"],
        help="Filter posts by task_difficulty",
    )
    c1.add_argument("--limit", type=int, default=None)

    c2 = sub.add_parser("eval-slot", help="Evaluate a single slot (before or after)")
    c2.add_argument("slot", choices=("before", "after"))
    g = c2.add_mutually_exclusive_group(required=True)
    g.add_argument("--greedy", action="store_true", help="Greedy decoding")
    g.add_argument("--best-of", type=int, dest="best_of", help="Best-of-N sampling")
    c2.add_argument("--temperature", type=float, default=0.65)
    c2.add_argument(
        "--difficulties",
        nargs="*",
        default=["easy", "medium", "hard"],
    )
    c2.add_argument("--limit", type=int, default=None)

    args = p.parse_args()
    from training.rl_loop import (
        evaluate_policy,
        load_posts,
        merge_slot,
        write_metrics_bundle,
    )

    if args.cmd == "eval-comparison":
        print("[rl_trainer] Loading model via inference (first run may download weights)…")
        import inference  # noqa: F401

        posts = load_posts(args.difficulties, args.limit)
        print(f"[rl_trainer] Evaluating {len(posts)} posts…")
        before = evaluate_policy(
            posts,
            lambda pr: __import__("inference")._call_llm(pr),
            label="greedy_baseline",
            best_of=1,
        )
        before["model_id"] = _model_id()
        after = evaluate_policy(
            posts,
            lambda pr: __import__("inference")._call_llm(pr),
            label=f"best_of_{args.best_of}",
            best_of=args.best_of,
            temperature=args.temperature,
        )
        after["model_id"] = _model_id()
        notes = (
            f"After policy = test-time best-of-{args.best_of} (max heuristic reward); "
            "no weight update. For true weight updates run ``training/lora_sft.py`` "
            "then ``eval-slot after --greedy`` with HF_ADAPTER_PATH set."
        )
        write_metrics_bundle(
            args.out,
            before=before,
            after=after,
            model_id=_model_id(),
            notes=notes,
        )
        print(f"[rl_trainer] Wrote {args.out}")
        print("[rl_trainer] before:", before)
        print("[rl_trainer] after: ", after)
        return

    # eval-slot
    print("[rl_trainer] Loading model…")
    import inference  # noqa: F401

    posts = load_posts(args.difficulties, args.limit)
    if args.greedy:
        m = evaluate_policy(
            posts,
            lambda pr: __import__("inference")._call_llm(pr),
            label="greedy",
            best_of=1,
        )
    else:
        m = evaluate_policy(
            posts,
            lambda pr: __import__("inference")._call_llm(pr),
            label=f"best_of_{args.best_of}",
            best_of=int(args.best_of),
            temperature=args.temperature,
        )
    m["model_id"] = _model_id()
    merge_slot(args.out, args.slot, m)
    print(f"[rl_trainer] Updated '{args.slot}' in {args.out}")
    print(m)


if __name__ == "__main__":
    main()
