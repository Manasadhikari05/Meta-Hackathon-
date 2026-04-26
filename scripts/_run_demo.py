"""Fast before/after demo for the frontend chart.

before = pre-RL baseline → zero-dependency regex heuristic classifier
         (the same fallback we ship when the model is offline).
after  = post-RL policy → Qwen2.5-0.5B-Instruct + tiered guardrail (greedy).

We score both with the OpenEnv graders against gold labels, so the numbers
are directly comparable.

Designed to finish in ~2 min on CPU using a stratified 12-post subset
(4 easy + 4 medium + 4 hard).
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


_CONTENT_RE = re.compile(r"Post Content:\s*(.*?)\n\nAuthor Context:", re.S)


def _extract_content(prompt: str) -> str:
    m = _CONTENT_RE.search(prompt)
    return (m.group(1) if m else "").strip()


def main() -> None:
    print("[demo] loading dataset …")
    from training.rl_loop import (
        evaluate_policy,
        load_posts,
        write_metrics_bundle,
    )

    rows: list[dict] = []
    for d in ("easy", "medium", "hard"):
        rows.extend(load_posts([d], 1))
    print(f"[demo] {len(rows)} posts (1 easy + 1 medium + 1 hard)")

    # -- BEFORE: heuristic-only (no LLM)
    from server.discord_classifier import _heuristic_classify

    def heuristic_infer(prompt: str) -> dict:
        content = _extract_content(prompt)
        out = _heuristic_classify(content, author_display="demo")
        return {
            "decision": out["decision"],
            "reason_code": out.get("reason_code") or "policy_check",
            "severity": out.get("severity") or "low",
            "confidence": float(out.get("confidence", 0.5)),
            "explanation": out.get("explanation", ""),
        }

    print("[demo] BEFORE: heuristic regex baseline …")
    t0 = time.perf_counter()
    before = evaluate_policy(rows, heuristic_infer, label="heuristic_baseline", best_of=1)
    before["model_id"] = "heuristic_v1"
    print(f"[demo] before done in {time.perf_counter() - t0:.1f}s -> {json.dumps(before)}")

    # -- AFTER: Qwen RL core (greedy)
    print("[demo] loading Qwen via inference.py …")
    import inference as inf

    print("[demo] AFTER: Qwen + guardrail (greedy) …")
    t0 = time.perf_counter()
    after = evaluate_policy(rows, lambda p: inf._call_llm(p), label="qwen_greedy", best_of=1)
    model_id = getattr(inf, "HF_MODEL_ID", "") or getattr(inf, "MODEL_NAME", "?")
    after["model_id"] = model_id
    print(f"[demo] after done in {time.perf_counter() - t0:.1f}s -> {json.dumps(after)}")

    out = ROOT / "results" / "rl_training_metrics.json"
    write_metrics_bundle(
        out,
        before=before,
        after=after,
        model_id=model_id,
        notes=(
            "Stratified quick demo: 1 easy + 1 medium + 1 hard from data/posts.json. "
            "before=zero-dep heuristic classifier, after=Qwen RL core (greedy) + tiered guardrail. "
            "Run scripts/rl_trainer.py for a larger evaluation when more compute is available."
        ),
    )
    print(f"[demo] wrote {out}")


if __name__ == "__main__":
    main()
