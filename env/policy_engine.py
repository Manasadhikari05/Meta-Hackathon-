"""
Adaptive policy layer on top of base LLM moderation.

This does not retrain the hosted model weights. Instead it learns lightweight
override rules from user feedback and applies them before returning a verdict.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

_STORE_PATH = Path(__file__).resolve().parents[1] / "data" / "policy_memory.json"

_state = {
    "rules": [],
    "stats": {
        "total_feedback": 0,
        "low_rating_feedback": 0,
        "rules_applied": 0,
        "rules_created": 0,
    },
}


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    stop = {"this", "that", "with", "from", "your", "have", "just", "really", "very", "much"}
    return [w for w in words if w not in stop]


def _save() -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(_state, indent=2), encoding="utf-8")


def load_state() -> None:
    if _STORE_PATH.exists():
        try:
            data = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                _state.update(data)
        except Exception:
            pass


def get_stats() -> dict:
    return {
        "rules": len(_state["rules"]),
        **_state["stats"],
    }


def get_rules(limit: int = 50) -> list[dict]:
    return list(reversed(_state["rules"][-limit:]))


def apply_policy(content: str, verdict: dict) -> dict:
    text = content.lower()
    for rule in reversed(_state["rules"]):
        if rule["keyword"] in text:
            tuned = dict(verdict)
            tuned["decision"] = rule["desired_decision"]
            tuned["policy_override"] = {
                "keyword": rule["keyword"],
                "source": "feedback_rule",
            }
            if tuned["decision"] == "approve":
                tuned["reason_code"] = "clean"
                tuned["severity"] = "low"
            elif tuned["decision"] == "remove":
                if tuned.get("reason_code") == "clean":
                    tuned["reason_code"] = "harassment"
                tuned["severity"] = "high"
            else:
                tuned["severity"] = "medium"

            tuned["confidence"] = min(0.99, round(float(tuned.get("confidence", 0.5)) + 0.08, 3))
            tuned["explanation"] = f"Policy override learned from moderator feedback ({rule['keyword']})."
            _state["stats"]["rules_applied"] += 1
            _save()
            return tuned
    return verdict


def learn_from_feedback(payload: dict) -> dict:
    _state["stats"]["total_feedback"] += 1
    rating = int(payload.get("rating", 5))
    desired = payload.get("desired_decision")
    current = payload.get("decision")
    content = payload.get("content", "")

    if rating <= 6:
        _state["stats"]["low_rating_feedback"] += 1

    # Only learn a correction rule when user specifies desired action and disagrees.
    if desired and desired in {"approve", "remove", "escalate"} and desired != current:
        tokens = _tokenize(content)
        keyword = tokens[0] if tokens else "comment"
        _state["rules"].append(
            {
                "keyword": keyword,
                "desired_decision": desired,
                "from_decision": current,
                "rating": rating,
                "comment": payload.get("comment"),
                "created_at": int(time.time()),
            }
        )
        _state["stats"]["rules_created"] += 1
        _save()
        return {"learned": True, "keyword": keyword}

    _save()
    return {"learned": False}
