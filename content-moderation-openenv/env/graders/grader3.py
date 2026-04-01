"""Deterministic grader for task 3 (hard edge cases with explanation scoring)."""

from difflib import SequenceMatcher

from env.graders.grader1 import grade as base_grade


def grade(action, gold) -> float:
    """
    Task 3 score:
    - 70% base moderation quality
    - 30% explanation quality
    """
    score = base_grade(action, gold) * 0.70

    if gold.get("requires_explanation", False):
        explanation = getattr(action, "explanation", "") or ""
        gold_explanation = gold.get("explanation", "") or ""

        if explanation.strip():
            keyword_score = _keyword_overlap_score(explanation, gold_explanation)
            similarity_score = SequenceMatcher(
                None,
                explanation.lower().strip(),
                gold_explanation.lower().strip(),
            ).ratio()

            explanation_score = 0.5 * keyword_score + 0.5 * similarity_score
            score += 0.30 * explanation_score

    return round(min(1.0, max(0.0, score)), 4)


def _keyword_overlap_score(pred_explanation: str, gold_explanation: str) -> float:
    """
    Simple deterministic overlap without needing explanation_keywords in dataset.
    """
    pred_words = {
        w.strip(".,!?:;\"'()[]{}").lower()
        for w in pred_explanation.split()
        if len(w.strip(".,!?:;\"'()[]{}")) > 2
    }
    gold_words = {
        w.strip(".,!?:;\"'()[]{}").lower()
        for w in gold_explanation.split()
        if len(w.strip(".,!?:;\"'()[]{}")) > 2
    }

    if not gold_words:
        return 0.0

    overlap = len(pred_words & gold_words)
    return overlap / len(gold_words)