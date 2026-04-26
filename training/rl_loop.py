"""Rollout evaluation + optional test-time policy improvement for the Qwen
moderation agent.

This tightens the project’s “RL loop”: the model acts on posts, receives a
scalar reward from the same heuristic graders used by OpenEnv tasks, and we
aggregate metrics suitable for before/after dashboards.

``best_of_n`` is a lightweight *inference-time* improvement (sample multiple
actions, keep the highest-reward one). It does not update weights; for that
see ``training/lora_sft.py`` + ``HF_ADAPTER_PATH`` in ``.env``.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from env.graders._shared import normalize_decision
from env.graders.grader1 import grade as grade_task1
from env.graders.grader2 import grade as grade_task2
from env.graders.grader3 import grade as grade_task3
from env.models import ModerationAction

_POSTS_PATH = Path(__file__).resolve().parents[1] / "data" / "posts.json"


def _task_id_for_difficulty(difficulty: str) -> str:
    d = (difficulty or "easy").lower()
    return {"easy": "task1", "medium": "task2", "hard": "task3"}.get(d, "task1")


def _grade_fn(task_id: str):
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


def _default_instructions(task_id: str) -> str:
    return (
        "Moderate this post: choose approve, remove, or escalate with reason_code, "
        "severity, and confidence per policy."
    )


def _dict_to_action(raw: dict) -> ModerationAction:
    return ModerationAction(
        decision=raw["decision"],
        reason_code=raw["reason_code"],
        severity=raw["severity"],
        confidence=float(raw.get("confidence", 0.5)),
        explanation=(raw.get("explanation") or "")[:500] or None,
    )


def _decision_match(pred: dict, gold_label: dict) -> bool:
    p = normalize_decision(pred.get("decision"))
    g = normalize_decision(gold_label.get("decision"))
    return p == g


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
    """Return (best_action_dict, best_reward, n_calls).

    Picks the candidate with highest heuristic grader score. Ties broken by
    first candidate.
    """
    grade = _grade_fn(task_id)
    best: dict | None = None
    best_r = -1.0
    calls = 0
    # Always include one greedy decode as the first candidate (stable anchor).
    candidates: List[dict] = [_call_llm_greedy(prompt)]
    calls += 1
    for _ in range(max(0, n - 1)):
        candidates.append(_call_llm_sample(prompt, temperature))
        calls += 1

    for cand in candidates:
        try:
            act = _dict_to_action(cand)
            r = float(grade(act, gold))
        except Exception:
            r = 0.001
        if r > best_r:
            best_r = r
            best = cand
    return best or candidates[0], best_r, len(candidates)


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
            "policy": f"greedy" if best_of <= 1 else f"best_of_{best_of}",
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
            act = _dict_to_action(raw)
            r = float(grade(act, gold))
        except Exception:
            r = 0.001
        rewards.append(r)
        latencies.append(dt_ms)
        if _decision_match(raw, gold):
            dec_hits += 1

    n_posts = len(posts)
    n = n_posts or 1
    wall_ms = (time.perf_counter() - t0_wall) * 1000
    return {
        "policy": f"greedy" if best_of <= 1 else f"best_of_{best_of}",
        "label": label,
        "n_posts": n_posts,
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


def write_metrics_bundle(
    path: Path,
    *,
    before: Dict[str, Any],
    after: Dict[str, Any],
    model_id: str,
    notes: str = "",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    eff = {}
    if before.get("n_posts") and after.get("n_posts"):
        eff = {
            "mean_reward_delta": round(
                float(after["mean_reward"]) - float(before["mean_reward"]), 4
            ),
            "accuracy_delta_pp": round(
                (float(after["decision_accuracy"]) - float(before["decision_accuracy"]))
                * 100,
                2,
            ),
            "latency_ratio": round(
                float(after["mean_latency_ms"]) / max(1.0, float(before["mean_latency_ms"])),
                3,
            ),
        }
    payload = {
        "loaded": True,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_id": model_id,
        "before": before,
        "after": after,
        "efficiency": eff,
        "notes": notes,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def merge_slot(path: Path, slot: Literal["before", "after"], metrics: Dict[str, Any]) -> None:
    """Update only ``before`` or ``after`` in an existing JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"loaded": True, "model_id": "", "before": {}, "after": {}}
    data[slot] = metrics
    mid = metrics.get("model_id") or data.get("model_id")
    if mid:
        data["model_id"] = mid
    data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if data.get("before") and data.get("after"):
        b, a = data["before"], data["after"]
        data["efficiency"] = {
            "mean_reward_delta": round(float(a["mean_reward"]) - float(b["mean_reward"]), 4),
            "accuracy_delta_pp": round(
                (float(a["decision_accuracy"]) - float(b["decision_accuracy"])) * 100, 2
            ),
            "latency_ratio": round(
                float(a["mean_latency_ms"]) / max(1.0, float(b["mean_latency_ms"])), 3
            ),
        }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
