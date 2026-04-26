def grade(action: dict, ground_truth: dict, task_id: str) -> tuple[float, str]:
    """
    Grade an action against ground truth for content moderation decisions.
    
    Args:
        action: {decision, reason_code, severity, confidence, explanation}
        ground_truth: {decision, reason_code, severity}
        task_id: "task1", "task2", or "task3"
    
    Returns:
        (score: float, reasoning: str)
    """
    score = 0.0
    
    # Decision scoring
    action_decision = action.get("decision", "")
    gt_decision = ground_truth.get("decision", "")
    
    if action_decision == gt_decision:
        score += 0.50
    else:
        # Check for adjacent pairs: (remove <-> escalate), (approve <-> escalate)
        adjacent_pairs = [{"remove", "escalate"}, {"approve", "escalate"}]
        if {action_decision, gt_decision} in adjacent_pairs:
            score += 0.20
    
    # Reason code scoring
    action_reason = action.get("reason_code", "")
    gt_reason = ground_truth.get("reason_code", "")
    
    if action_reason == gt_reason:
        score += 0.30
    else:
        # Check same broad category
        categories = {
            "abuse": {"hate_speech", "harassment"},
            "harm": {"self_harm", "violence"},
            "safe": {"clean"},
            "info": {"spam", "misinformation"},
            "adult": {"sexual_content"}
        }
        action_cat = None
        gt_cat = None
        for cat, codes in categories.items():
            if action_reason in codes:
                action_cat = cat
            if gt_reason in codes:
                gt_cat = cat
        if action_cat is not None and action_cat == gt_cat:
            score += 0.12
    
    # Severity scoring
    action_severity = action.get("severity")
    gt_severity = ground_truth.get("severity")
    
    if action_severity == gt_severity:
        score += 0.20
    else:
        # Check if off by one level
        if action_severity is not None and gt_severity is not None:
            if abs(action_severity - gt_severity) == 1:
                score += 0.10
    
    # Task-specific adjustments
    if task_id == "task2":
        confidence = action.get("confidence", 0.0)
        if action_decision == gt_decision:
            score *= confidence
        else:
            score *= (1 - confidence)
    elif task_id == "task3":
        explanation = action.get("explanation", "")
        expl_words = explanation.split()
        # Length bonus: up to 0.15 for longer explanations (capped at ~50 words)
        length_bonus = min(0.15, len(expl_words) * 0.003)
        # Keyword overlap bonus: up to 0.15
        # Extract keywords from reason code (split by underscore)
        gt_reason_keywords = set(gt_reason.split("_"))
        expl_lower = explanation.lower()
        overlap_count = sum(1 for kw in gt_reason_keywords if kw in expl_lower)
        overlap_bonus = min(0.15, overlap_count * 0.075)
        score += length_bonus + overlap_bonus
    
    # Penalty
    if action_decision == "approve" and gt_decision == "remove" and gt_reason in {"hate_speech", "violence", "self_harm"}:
        score -= 0.20
    
    # Clamp to (0.001, 0.999)
    score = max(0.001, min(0.999, score))
    
    # Generate reasoning
    reasoning = f"Score {score:.3f} based on decision match={action_decision==gt_decision}, reason_code match={action_reason==gt_reason}, severity match={action_severity==gt_severity}."
    
    return (round(score, 3), reasoning)