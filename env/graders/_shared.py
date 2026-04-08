# common grading helpers

_DECISION_NORMALIZE = {
    "approve": "allow",
    "allow": "allow",
    "escalate": "flag_for_review",
    "flag_for_review": "flag_for_review",
    "remove": "remove",
}

_REASON_NORMALIZE = {
    "clean": "safe",
    "harassment": "abuse",
    "sexual_content": "nsfw_spam",
}

_ADJACENT_DECISIONS = {
    ("remove", "flag_for_review"),
    ("flag_for_review", "remove"),
    ("allow", "flag_for_review"),
    ("flag_for_review", "allow"),
}

_REASON_FAMILIES = [
    {"abuse", "harassment", "insult", "mild_abuse", "borderline_abuse", "condescending", "aggressive"},
    {"sarcasm", "mocking", "mixed_tone", "sarcasm_obfuscated", "obfuscated_sarcasm"},
    {"spam", "scam", "misinformation", "nsfw_spam"},
    {"safe", "criticism", "neutral_feedback", "balanced_feedback", "advice"},
    {"violence", "self_harm", "violent_abuse", "obfuscated_abuse"},
    {"hate_speech", "hate_generalization"},
]

_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}


def normalize_decision(value: str) -> str:
    return _DECISION_NORMALIZE.get(value, value)


def normalize_reason(value: str) -> str:
    return _REASON_NORMALIZE.get(value, value)


def is_adjacent(pred: str, gold: str) -> bool:
    return (pred, gold) in _ADJACENT_DECISIONS


def same_reason_family(pred: str, gold: str) -> bool:
    return any(pred in fam and gold in fam for fam in _REASON_FAMILIES)


def severity_diff(pred_sev: str, gold_sev: str) -> int:
    """Returns 0, 1, or 2. -1 if either value is unknown."""
    a = _SEVERITY_RANK.get(pred_sev)
    b = _SEVERITY_RANK.get(gold_sev)
    if a is None or b is None:
        return -1
    return abs(a - b)


def _clamp(score: float) -> float:
    """Ensure score is strictly within (0, 1) - not 0.0 or 1.0."""
    if score <= 0.0:
        return 0.001
    if score >= 1.0:
        return 0.999
    return score
