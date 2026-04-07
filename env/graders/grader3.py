# Grader for task 3 — hard edge cases.
#
# 70% base moderation score (reuses grader1), 30% explanation quality.

from difflib import SequenceMatcher

from env.graders.grader1 import grade as base_grade


def grade(action, gold) -> float:
    score = base_grade(action, gold) * 0.70

    if not gold.get("requires_explanation", False):
        return round(min(0.95, max(0.05, score)), 4)

    explanation = getattr(action, "explanation", "") or ""
    gold_explanation = gold.get("explanation", "") or ""

    if not explanation.strip():
        return round(min(0.95, max(0.05, score)), 4)

    kw_score = _keyword_overlap(explanation, gold_explanation)
    sim_score = SequenceMatcher(
        None,
        explanation.lower().strip(),
        gold_explanation.lower().strip(),
    ).ratio()

    score += 0.30 * (0.5 * kw_score + 0.5 * sim_score)
    return round(min(0.95, max(0.05, score)), 4)


def _keyword_overlap(pred: str, gold: str) -> float:
    """Word-level overlap between predicted and gold explanations."""
    strip_chars = ".,!?:;\"'()[]{}"
    pred_words = {w.strip(strip_chars).lower() for w in pred.split()
                  if len(w.strip(strip_chars)) > 2}
    gold_words = {w.strip(strip_chars).lower() for w in gold.split()
                  if len(w.strip(strip_chars)) > 2}
    if not gold_words:
        return 0.0
    return len(pred_words & gold_words) / len(gold_words)