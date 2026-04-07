# Grader for task 2 — batch/medium difficulty.
#
# Weights: decision 40%, reason_code 35%, severity 15%, confidence 10%.
# More forgiving than task 1, also rewards calibrated confidence.

from env.graders._shared import (
    is_adjacent,
    normalize_decision,
    normalize_reason,
    same_reason_family,
    severity_diff,
)


def grade(action, gold) -> float:
    score = 0.0

    pred_dec = normalize_decision(getattr(action, "decision", None))
    gold_dec = normalize_decision(gold.get("decision"))

    pred_reason = normalize_reason(getattr(action, "reason_code", None))
    gold_reason = normalize_reason(gold.get("reason_code"))

    pred_sev = getattr(action, "severity", "medium")
    gold_sev = gold.get("severity", "medium")

    # decision — 40%
    if pred_dec == gold_dec:
        score += 0.40
    elif is_adjacent(pred_dec, gold_dec):
        score += 0.22

    # reason_code — 35%
    if pred_reason == gold_reason:
        score += 0.35
    elif same_reason_family(pred_reason, gold_reason):
        score += 0.15

    # severity — 15%
    diff = severity_diff(pred_sev, gold_sev)
    if diff >= 0:
        score += 0.15 * (1.0 - diff / 2)

    # confidence calibration — 10%
    conf = float(getattr(action, "confidence", 0.5))
    conf = min(1.0, max(0.0, conf))
    if pred_dec == gold_dec:
        score += 0.10 * conf
    else:
        score += 0.10 * (1.0 - conf)

    return round(min(0.9999, max(0.0001, score)), 4)