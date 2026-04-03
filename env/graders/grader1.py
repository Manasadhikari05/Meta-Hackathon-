# Grader for task 1 — single clear-cut post.
#
# Weights: decision 50%, reason_code 30%, severity 20%.
# Penalizes approving clearly harmful content.

from env.graders._shared import (
    is_adjacent,
    normalize_decision,
    normalize_reason,
    same_reason_family,
    severity_diff,
)

_SERIOUS_REASONS = {
    "hate_speech", "violence", "self_harm", "hate_generalization",
    "obfuscated_abuse", "violent_abuse", "harassment", "abuse",
}


def grade(action, gold) -> float:
    score = 0.0

    pred_dec = normalize_decision(getattr(action, "decision", None))
    gold_dec = normalize_decision(gold.get("decision"))

    pred_reason = normalize_reason(getattr(action, "reason_code", None))
    gold_reason = normalize_reason(gold.get("reason_code"))

    pred_sev = getattr(action, "severity", "medium")
    gold_sev = gold.get("severity", "medium")

    # decision — 50%
    if pred_dec == gold_dec:
        score += 0.50
    elif is_adjacent(pred_dec, gold_dec):
        score += 0.20

    # reason_code — 30%
    if pred_reason == gold_reason:
        score += 0.30
    elif same_reason_family(pred_reason, gold_reason):
        score += 0.12

    # severity — 20%
    diff = severity_diff(pred_sev, gold_sev)
    if diff >= 0:
        score += 0.20 * (1.0 - diff / 2)

    # penalty: approving something that should be removed (serious)
    if gold_dec == "remove" and pred_dec == "allow":
        if gold_reason in _SERIOUS_REASONS:
            score = max(0.0, score - 0.20)

    return round(min(1.0, max(0.0, score)), 4)