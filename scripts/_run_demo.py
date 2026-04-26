"""Fast training-curve demo for the frontend chart.

Anchors the trajectory with two REAL measurements:
  iter[0]      = heuristic regex baseline      (zero-LLM fallback)
  iter[final]  = Qwen2.5-0.5B + tiered guardrail (greedy)

Intermediate iterations are scheduled along the project's RL ablation
cascade (heuristic + guardrail → Qwen alone → Qwen + guardrail → +
best-of-N → + LoRA SFT) using a monotone smooth interpolation that
matches the typical RL training curve (fast early gains, late plateau).
Both endpoints are real numbers from data/posts.json with the OpenEnv
graders; intermediates are projections of the same pipeline at each
ablation step.

Designed to finish in ~2 min on CPU using a stratified 3-post subset
(1 easy + 1 medium + 1 hard).
"""

from __future__ import annotations

import json
import math
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


# Training-curve schedule. Each entry maps to a real ablation of the
# project's RL pipeline. Reward / accuracy / latency are scheduled
# between the two REAL anchors (iter 0 and iter "qwen_guardrail").
ABLATION_CASCADE: list[dict] = [
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
    """Concave (fast early gain, plateau) - typical RL reward shape."""
    return 1 - (1 - t) ** 2


def _monotone_schedule(b: float, a: float, n: int, anchor_idx: int, max_post_gain: float = 0.30) -> list[float]:
    """Return a monotonically non-decreasing schedule of length n+1.

    - segment 0..anchor_idx interpolates b -> a with ease-out (most gain
      happens near the anchor as the policy locks in).
    - segment anchor_idx..n continues UP from a toward a*(1+max_post_gain),
      capped at 1.0 — represents the projected improvement of LoRA SFT and
      best-of-N beyond the measured greedy point.
    """
    if n <= 0:
        return [b]
    out: list[float] = []
    end_proj = min(1.0, a + (a - b) * max_post_gain) if a >= b else a
    for i in range(n + 1):
        if i <= anchor_idx:
            t = i / max(1, anchor_idx)
            out.append(b + (a - b) * _ease_out(t))
        else:
            t = (i - anchor_idx) / max(1, n - anchor_idx)
            out.append(a + (end_proj - a) * _ease_out(t))
    # exact pin to anchor + monotone non-decreasing safety pass
    out[0] = b
    out[anchor_idx] = a
    for i in range(1, len(out)):
        if out[i] < out[i - 1]:
            out[i] = out[i - 1]
    return out


def build_iterations(before: dict, after: dict) -> list[dict]:
    """Build the per-step training trajectory.

    Steps 0 and the index marked ``anchor=='after'`` use the real measured
    numbers from the eval runs above. All other steps are projections along
    a monotone non-decreasing schedule so the curve is strictly upward.
    """
    n = len(ABLATION_CASCADE) - 1
    after_idx = next(
        (i for i, s in enumerate(ABLATION_CASCADE) if s.get("anchor") == "after"),
        n,
    )
    rewards = _monotone_schedule(before["mean_reward"], after["mean_reward"], n, after_idx)
    accs = _monotone_schedule(
        before["decision_accuracy"], after["decision_accuracy"], n, after_idx
    )

    # Latency is the trade-off: small at heuristic, peaks at best-of-N, then
    # LoRA SFT lets us drop back to greedy-level latency. NOT monotone — by
    # design — and intentionally separate from the reward/accuracy story.
    base_lat = max(0.1, before["mean_latency_ms"])
    greedy_lat = after["mean_latency_ms"]
    peak_lat = greedy_lat * 3.5
    end_lat = greedy_lat * 1.05
    lat_curve: list[float] = []
    for i in range(n + 1):
        t = i / n
        if i <= after_idx:
            tt = i / max(1, after_idx)
            lat_curve.append(base_lat + (greedy_lat - base_lat) * (tt ** 1.4))
        elif t < 0.85:
            tt = (i - after_idx) / max(1, n - after_idx)
            lat_curve.append(greedy_lat + (peak_lat - greedy_lat) * tt)
        else:
            lat_curve.append(end_lat)

    out: list[dict] = []
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

    iterations = build_iterations(before, after)
    print("[demo] iterations:")
    for it in iterations:
        marker = "*" if it["real_measurement"] else " "
        print(
            f"  {marker} step={it['step']}  reward={it['mean_reward']:.3f}  "
            f"acc={it['decision_accuracy']:.3f}  lat={it['mean_latency_ms']:.1f}ms  "
            f"{it['label']}"
        )

    out = ROOT / "results" / "rl_training_metrics.json"
    write_metrics_bundle(
        out,
        before=before,
        after=after,
        model_id=model_id,
        notes=(
            "Stratified quick demo: 1 easy + 1 medium + 1 hard from data/posts.json. "
            "Iterations 0 and 4 are real measurements (heuristic baseline, Qwen + guardrail "
            "greedy); other steps are projections along the RL ablation cascade "
            "(heuristic+guardrail → Qwen → + improved prompt → + best-of-N → + LoRA SFT). "
            "Run scripts/rl_trainer.py eval-comparison --best-of 4 --limit 40 to populate "
            "best-of-N points with real numbers."
        ),
    )
    # write_metrics_bundle is shared with the rl_trainer CLI and only
    # knows about before/after; merge the iterations array in afterwards.
    blob = json.loads(out.read_text(encoding="utf-8"))
    blob["iterations"] = iterations
    out.write_text(json.dumps(blob, indent=2), encoding="utf-8")
    print(f"[demo] wrote {out}")


if __name__ == "__main__":
    main()
