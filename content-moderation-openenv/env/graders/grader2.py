"""Deterministic grader for task 2 (batch/medium difficulty)."""


def grade(action, gold) -> float:
    """
    Score medium-difficulty moderation with partial credit.

    Task 2 is more forgiving than task 1 and rewards calibrated confidence.

    Weights:
    - decision: 40%
    - reason_code: 35%
    - severity: 15%
    - confidence calibration: 10%
    """
    score = 0.0

    action_decision = _normalize_decision(getattr(action, "decision", None))
    gold_decision = _normalize_decision(gold.get("decision"))

    action_reason = _normalize_reason(getattr(action, "reason_code", None))
    gold_reason = _normalize_reason(gold.get("reason_code"))

    action_severity = getattr(action, "severity", "medium")
    gold_severity = gold.get("severity", "medium")

    # Decision (40%)
    if action_decision == gold_decision:
        score += 0.40
    elif _is_adjacent(action_decision, gold_decision):
        score += 0.22

    # Reason code (35%)
    if action_reason == gold_reason:
        score += 0.35
    elif _same_reason_family(action_reason, gold_reason):
        score += 0.15

    # Severity (15%)
    sev = {"low": 0, "medium": 1, "high": 2}
    if action_severity in sev and gold_severity in sev:
        diff = abs(sev[action_severity] - sev[gold_severity])
        score += 0.15 * (1.0 - diff / 2)

    # Confidence calibration (10%)
    conf = float(getattr(action, "confidence", 0.5))
    conf = min(1.0, max(0.0, conf))

    if action_decision == gold_decision:
        score += 0.10 * conf
    else:
        score += 0.10 * (1.0 - conf)

    return round(min(1.0, max(0.0, score)), 4)


def _normalize_decision(value: str):
    mapping = {
        "approve": "allow",
        "allow": "allow",
        "escalate": "flag_for_review",
        "flag_for_review": "flag_for_review",
        "remove": "remove",
    }
    return mapping.get(value, value)


def _normalize_reason(value: str):
    mapping = {
        "clean": "safe",
        "harassment": "abuse",
        "sexual_content": "nsfw_spam",
    }
    return mapping.get(value, value)


def _is_adjacent(pred: str, gold: str) -> bool:
    adjacent = {
        ("remove", "flag_for_review"),
        ("flag_for_review", "remove"),
        ("allow", "flag_for_review"),
        ("flag_for_review", "allow"),
    }
    return (pred, gold) in adjacent


def _same_reason_family(pred: str, gold: str) -> bool:
    families = [
        {"abuse", "harassment", "insult", "mild_abuse", "borderline_abuse", "condescending", "aggressive"},
        {"sarcasm", "mocking", "mixed_tone", "sarcasm_obfuscated", "obfuscated_sarcasm"},
        {"spam", "scam", "misinformation", "nsfw_spam"},
        {"safe", "criticism", "neutral_feedback", "balanced_feedback", "advice"},
        {"violence", "self_harm", "violent_abuse", "obfuscated_abuse"},
        {"hate_speech", "hate_generalization"},
    ]
    return any(pred in fam and gold in fam for fam in families)