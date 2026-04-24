"""
LLM-as-judge grader using llama3.2 via Ollama.

Replaces the hardcoded heuristic graders with a language model that reasons
about whether a moderation decision is appropriate given the post content,
author context, and task difficulty. Falls back to the heuristic grader if
Ollama is unreachable.
"""

import json
import os

import httpx

from env.graders._shared import _clamp

OLLAMA_URL   = os.getenv("OLLAMA_URL",        "http://localhost:11434")
AI_MODEL     = os.getenv("AI_GRADER_MODEL",   "llama3.2:latest")
TIMEOUT      = float(os.getenv("AI_GRADER_TIMEOUT", "60"))

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _prompt(action, post_row: dict, task_id: str) -> str:
    content      = post_row.get("content", "")
    platform     = post_row.get("platform", "unknown")
    author       = post_row.get("author", {})
    gold         = post_row.get("gold_label", {})
    thread       = post_row.get("thread_context", {})

    age        = author.get("account_age_days", "?")
    violations = author.get("prior_violations", 0)
    total      = author.get("total_posts", 0)
    topic      = thread.get("topic", "unknown")

    pred_decision   = getattr(action, "decision",   "?")
    pred_reason     = getattr(action, "reason_code","?")
    pred_severity   = getattr(action, "severity",   "?")
    pred_confidence = float(getattr(action, "confidence", 0.5))
    pred_explanation = (getattr(action, "explanation", "") or "").strip()

    gold_decision  = gold.get("decision",  "?")
    gold_reason    = gold.get("reason_code", "?")
    gold_severity  = gold.get("severity",  "?")
    gold_expl      = (gold.get("explanation", "") or "").strip()
    needs_expl     = gold.get("requires_explanation", False)

    # Task-specific notes
    task_note = {
        "task1": "This is a straightforward, clear-cut post.",
        "task2": (
            "This is a medium-difficulty batch post. Confidence calibration matters: "
            "high confidence on a correct decision is rewarded; high confidence on a "
            "wrong decision is penalised."
        ),
        "task3": (
            "This is a hard edge case (sarcasm, obfuscation, or implicit harm). "
            "Explanation quality contributes 30 % of the total score. "
            "Evaluate whether the explanation correctly identifies the harm pattern."
        ),
    }.get(task_id, "")

    explanation_block = ""
    if pred_explanation:
        explanation_block = f"\n  explanation  : \"{pred_explanation}\""

    gold_expl_block = ""
    if gold_expl:
        gold_expl_block = f"\n  explanation  : \"{gold_expl}\""

    expl_note = ""
    if needs_expl and not pred_explanation:
        expl_note = "\nWARNING: This post requires an explanation but none was provided. Penalise accordingly."

    return f"""You are a strict content moderation judge. Score a submitted moderation decision.

TASK NOTE: {task_note}

--- POST ---
content  : "{content}"
platform : {platform}
topic    : {topic}
author   : {age} days old, {violations} prior violation(s), {total} total posts

--- SUBMITTED DECISION ---
  action       : {pred_decision}
  reason_code  : {pred_reason}
  severity     : {pred_severity}
  confidence   : {pred_confidence:.2f}{explanation_block}

--- GOLD STANDARD (correct answer) ---
  action       : {gold_decision}
  reason_code  : {gold_reason}
  severity     : {gold_severity}{gold_expl_block}{expl_note}

--- SCORING RUBRIC ---
Start at 0.0, add points:
  +0.50  decision exactly matches gold
  +0.20  decision is adjacent (remove↔escalate or approve↔escalate)
  +0.30  reason_code exactly matches (or is semantically equivalent)
  +0.12  reason_code is in the same broad category (abuse/spam/harm/safe)
  +0.20  severity exactly matches
  +0.10  severity is off by one level
  -0.20  PENALTY: approved content that gold says should be removed AND reason is serious harm
For task2 confidence bonus (+0.10 × confidence if correct, +0.10 × (1−confidence) if wrong).
For task3 add up to +0.30 for explanation quality (keyword overlap + coherence with gold explanation).
Clamp final score to [0.01, 0.99].

Respond with valid JSON only — no markdown, no extra text:
{{"score": <float 0.01-0.99>, "reasoning": "<one concise sentence explaining the score>"}}"""


# ---------------------------------------------------------------------------
# Ollama call
# ---------------------------------------------------------------------------

def _call_ollama(prompt: str) -> dict:
    resp = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model":    AI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream":   False,
            "format":   "json",
            "options":  {"temperature": 0.05, "num_predict": 200},
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    raw = resp.json()["message"]["content"]
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def grade(action, post_row: dict, task_id: str = "task1") -> tuple[float, str]:
    """
    Grade a moderation action using llama3.2 as judge.

    Args:
        action:   ModerationAction (or any object with .decision, .reason_code, etc.)
        post_row: Full post dict from posts.json (includes gold_label, content, author…)
        task_id:  "task1" | "task2" | "task3"

    Returns:
        (score, reasoning) — score is strictly in (0, 1); reasoning is a human-readable
        sentence from the LLM explaining why it gave that score.
    """
    try:
        result    = _call_ollama(_prompt(action, post_row, task_id))
        score     = float(result.get("score", 0.5))
        reasoning = result.get("reasoning", "").strip()
        print(f"[ai_grader] {task_id} score={score:.3f}  — {reasoning}")
        return _clamp(score), reasoning

    except Exception as exc:
        print(f"[ai_grader] Ollama error ({exc!r}), falling back to heuristic grader.")
        return _heuristic_fallback(action, post_row, task_id)


def _heuristic_fallback(action, post_row: dict, task_id: str) -> tuple[float, str]:
    gold = post_row.get("gold_label", {})
    if task_id == "task3":
        from env.graders.grader3 import grade as g
        score = g(action, gold)
    elif task_id == "task2":
        from env.graders.grader2 import grade as g
        score = g(action, gold)
    else:
        from env.graders.grader1 import grade as g
        score = g(action, gold)
    return score, "Scored by heuristic grader (Ollama unavailable)."
