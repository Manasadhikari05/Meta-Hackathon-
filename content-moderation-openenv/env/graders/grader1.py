"""Deterministic grader for task 1 (single clear-cut post)."""


def grade(action, gold) -> float:
    """
    Score easy moderation cases.

    Weights:
    - decision: 50%
    - reason_code: 30%
    - severity: 20%
    """
    score = 0.0

    action_decision = _normalize_decision(getattr(action, "decision", None))
    gold_decision = _normalize_decision(gold.get("decision"))

    action_reason = _normalize_reason(getattr(action, "reason_code", None))
    gold_reason = _normalize_reason(gold.get("reason_code"))

    action_severity = getattr(action, "severity", "medium")
    gold_severity = gold.get("severity", "medium")

    # Decision (50%)
    if action_decision == gold_decision:
        score += 0.50
    elif _is_adjacent(action_decision, gold_decision):
        score += 0.20

    # Reason code (30%)
    if action_reason == gold_reason:
        score += 0.30
    elif _same_reason_family(action_reason, gold_reason):
        score += 0.12

    # Severity (20%)
    sev = {"low": 0, "medium": 1, "high": 2}
    if action_severity in sev and gold_severity in sev:
        diff = abs(sev[action_severity] - sev[gold_severity])
        score += 0.20 * (1.0 - diff / 2)

    # Extra penalty for allowing serious harmful content
    serious_reasons = {
        "hate_speech",
        "violence",
        "self_harm",
        "hate_generalization",
        "obfuscated_abuse",
        "violent_abuse",
        "harassment",
        "abuse",
    }
    if gold_decision == "remove" and action_decision == "allow":
        if gold_reason in serious_reasons:
            score = max(0.0, score - 0.20)

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