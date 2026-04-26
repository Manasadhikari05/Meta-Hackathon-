"""Classify Discord messages via OpenAI moderator, local/cloud RL inference, or a
zero-dependency heuristic fallback.

Order chosen so the bot never silently drops a message, even if no API key /
local model is available.
"""

from __future__ import annotations

import os
import re
from typing import Any, Tuple


# --- Heuristic (no external deps) ---------------------------------------------------

_HARD_REMOVE_PATTERNS = [
    # Slurs / extreme hate-speech tokens kept short on purpose; expand as needed.
    r"\bn[i1]gg(?:er|a)\b",
    r"\bf[a@]gg(?:[o0]t)?\b",
    r"\bk[i1]ke\b",
    r"\bkys\b",                # "kill yourself"
    r"\bkill\s+yourself\b",
    r"\bgo\s+die\b",
]

_ESCALATE_PATTERNS = [
    r"\b(?:i\s*want\s*to|gonna|going\s*to)\s*(?:kill|murder|hurt|stab|shoot)\b",
    r"\bbomb(?:ing)?\b",
    r"\bsuicid\w*\b",
    r"\bself[-\s]?harm\b",
    r"\b(?:doxx?|leak)\s*(?:your|his|her|their)?\s*(?:address|number|info)\b",
]

_FLAG_PATTERNS = [
    r"\b(?:fuck|shit|bitch|asshole|dick|cunt)\b",
    r"\bidiot\b",
    r"\bstupid\b",
    r"\bhate\s+you\b",
]


def _heuristic_classify(content: str, author_display: str) -> dict[str, Any]:
    text = (content or "").lower()

    def _any(patterns: list[str]) -> bool:
        return any(re.search(p, text) for p in patterns)

    if _any(_HARD_REMOVE_PATTERNS):
        decision = "remove"
        reason = "hate_or_harassment"
        severity = "high"
        confidence = 0.9
        explanation = "Heuristic matched hate-speech / harassment terms."
    elif _any(_ESCALATE_PATTERNS):
        decision = "escalate"
        reason = "self_harm_or_threats"
        severity = "high"
        confidence = 0.85
        explanation = "Heuristic matched self-harm / threat / doxx patterns — sent to mod log."
    elif _any(_FLAG_PATTERNS):
        decision = "approve"
        reason = "mild_profanity"
        severity = "low"
        confidence = 0.55
        explanation = "Heuristic flagged mild profanity but allowed."
    else:
        decision = "approve"
        reason = "clean"
        severity = "low"
        confidence = 0.6
        explanation = "Heuristic found no policy hits."

    return {
        "post_id": "",
        "content": content,
        "platform": "discord",
        "decision": decision,
        "reason_code": reason,
        "severity": severity,
        "confidence": float(confidence),
        "explanation": explanation,
        "model": "heuristic_v1",
    }


# --- Optional: full RL / local-model path ------------------------------------------

def _rl_classify(content: str, author_display: str) -> dict[str, Any]:
    """Use inference._call_llm (Qwen/Mistral/OpenAI per .env). Heavy — may download a model."""
    from inference import _call_llm

    prompt = (
        "Classify this Discord server message for content moderation.\n\n"
        f"Author: {author_display}\n"
        f"Message: {content}\n\n"
        "Respond with ONLY the JSON classification."
    )
    action = _call_llm(prompt)
    model = (
        os.getenv("HF_MODEL_ID", "")
        if str(os.getenv("USE_LOCAL_LLM", "true")).lower() in ("true", "1", "yes")
        else os.getenv("MODEL_NAME", "gpt-4o-mini")
    )
    return {
        "post_id": "",
        "content": content,
        "platform": "discord",
        "decision": action["decision"],
        "reason_code": action["reason_code"],
        "severity": action["severity"],
        "confidence": float(action["confidence"]),
        "explanation": action.get("explanation", ""),
        "model": model or "rl_inference",
    }


# --- Reconcile (guardrail) ---------------------------------------------------------
#
# Small local models (e.g. Qwen 0.5B) frequently hallucinate "remove" on plain
# greetings or casual chat. We can't afford to delete every "hello" on Discord.
# So after the model gives its decision, we run the heuristic and reconcile:
#
#   * If heuristic says "approve / clean" AND message has no risk markers
#     (no slurs, no links, no threat words, no profanity), but the model said
#     remove/escalate -> trust the heuristic and approve.
#   * If heuristic says "remove" (hard slur / kys / explicit threat) but the
#     model said approve -> trust the heuristic and remove.
# In both cases we annotate the explanation so it's transparent in the UI.

# "Soft" markers: borderline insults / casual profanity. These should NOT cause
# auto-delete on a server. If the model says remove, we downgrade to escalate.
_SOFT_RISK_RE = re.compile(
    r"(?:\bstupid\b|\bidiot\b|\bdumb\b|\btrash\b|\bloser\b|"
    r"\bfuck|\bshit\b|\bbitch\b|\bdick\b|\basshole\b|\bhate\s+you\b)",
    re.IGNORECASE,
)
# "Hard" markers: things that should clearly auto-remove or escalate without debate.
_HARD_RISK_RE = re.compile(
    r"(?:\bcunt\b|\bnigg|\bfagg|\bkike\b|\bkys\b|\bgo\s+kill\s+yourself\b|"
    r"\bgo\s+die\b|\brape\b|\bbomb\b|\bdoxx?\b|"
    r"\bi(?:'ll| will)\s+(?:kill|murder|stab|shoot)\b|"
    r"\bsuicid\w*\b|\bself[- ]?harm\b)",
    re.IGNORECASE,
)
# Spam-ish markers (links, scam words).
_SPAM_RISK_RE = re.compile(
    r"(?:https?://|www\.|\.com\b|\.io\b|\.net\b|\bscam\b|\bphish\w*\b)",
    re.IGNORECASE,
)


def _risk_tier(content: str) -> str:
    """Return one of: 'hard' | 'soft' | 'spam' | 'none'."""
    if not content:
        return "none"
    if _HARD_RISK_RE.search(content):
        return "hard"
    if _SPAM_RISK_RE.search(content):
        return "spam"
    if _SOFT_RISK_RE.search(content):
        return "soft"
    return "none"


def _reconcile(rl_result: dict[str, Any], heuristic_result: dict[str, Any], content: str) -> dict[str, Any]:
    """Sanity-check the model decision against simple deterministic rules.

    Goal: small models (Qwen 0.5B) tend to mash everything into `remove`. We
    make sure that:
      * benign chat (no risk markers anywhere)              -> approve
      * mild profanity / borderline insults  (soft markers) -> escalate (mod review)
      * hard slurs / explicit threats        (hard markers) -> remove
      * spam-looking messages (links etc.)                  -> escalate at minimum
    """
    rl_decision = rl_result.get("decision", "escalate")
    rl_reason = rl_result.get("reason_code", "harassment")
    heur_decision = heuristic_result.get("decision", "approve")
    tier = _risk_tier(content)
    original_explain = (rl_result.get("explanation") or "").strip()

    def _override(decision: str, reason: str, severity: str, note: str) -> dict[str, Any]:
        out = dict(rl_result)
        out["decision"] = decision
        out["reason_code"] = reason
        out["severity"] = severity
        out["explanation"] = (
            f"{note} (model said: {rl_decision}/{rl_reason} — {original_explain or 'n/a'})"
        )[:200]
        return out

    # 1. Hard violations: trust heuristic, force remove (even if model approves).
    if tier == "hard" or heur_decision == "remove":
        if rl_decision == "remove":
            return rl_result  # already correct
        return _override("remove", heuristic_result.get("reason_code", "harassment"),
                         "high", "removed (hard violation matched)")

    # 2. Heuristic flagged escalate-worthy threats / self-harm directly.
    if heur_decision == "escalate":
        if rl_decision == "remove":
            # Could be right (real threat) — keep model's stricter call.
            return rl_result
        if rl_decision == "approve":
            return _override("escalate",
                             heuristic_result.get("reason_code", "violence"),
                             heuristic_result.get("severity", "high"),
                             "escalated (heuristic detected threat/self-harm pattern)")
        return rl_result  # already escalate

    # 3. Soft markers: borderline insult / casual profanity. Don't auto-delete.
    if tier == "soft":
        if rl_decision == "remove":
            return _override("escalate", "harassment", "medium",
                             "escalated (soft profanity/insult — sent for human review)")
        if rl_decision == "approve":
            # Soft markers should at least be flagged for review.
            return _override("escalate", "harassment", "low",
                             "escalated (soft profanity/insult — flagged for review)")
        return rl_result  # already escalate

    # 4. Spam-ish markers (links, scam) — escalate, don't delete blindly.
    if tier == "spam":
        if rl_decision == "remove":
            return _override("escalate", "spam", "medium",
                             "escalated (link/spam-like — sent for human review)")
        if rl_decision == "approve":
            return _override("escalate", "spam", "low",
                             "escalated (link present — flagged for review)")
        return rl_result

    # 5. tier == "none": message has no risk markers anywhere.
    #    Trust heuristic over a hallucinating small model.
    if rl_decision in ("remove", "escalate"):
        return _override("approve", "clean", "low",
                         "approved (no risk markers in message — overrode model false positive)")
    return rl_result


# --- Public entry point ------------------------------------------------------------

def _has_openai_key() -> bool:
    k = os.getenv("OPENAI_API_KEY", "").strip()
    return bool(k) and not k.lower().startswith("sk-your-") and k != "REPLACE_ME"


def classify_discord_message(content: str, author_display: str) -> Tuple[dict[str, Any], str]:
    """
    Returns (moderation_dict, source_label).

    DISCORD_CLASSIFIER:
        heuristic  -> regex-based, no network, no model. Always works. (Default)
        moderator  -> OpenAI moderator (needs valid OPENAI_API_KEY).
        rl         -> inference._call_llm (local HF or OpenAI per env).
        auto       -> rl if local model usable, else moderator if key set, else heuristic.
    """
    explicit = os.getenv("DISCORD_CLASSIFIER", "heuristic").strip().lower()
    use_local = str(os.getenv("USE_LOCAL_LLM", "false")).strip().lower() in ("true", "1", "yes", "y")

    def _moderator() -> Tuple[dict[str, Any], str]:
        from env.moderator import moderate
        return moderate(content, "discord"), "openai_moderator"

    if explicit == "heuristic":
        return _heuristic_classify(content, author_display), "heuristic"

    if explicit == "moderator":
        try:
            return _moderator()
        except Exception as exc:
            return _heuristic_classify(content, author_display), f"heuristic_fallback:moderator_failed:{exc}"

    if explicit == "rl":
        try:
            rl = _rl_classify(content, author_display)
            heur = _heuristic_classify(content, author_display)
            reconciled = _reconcile(rl, heur, content)
            source = "rl_inference"
            if reconciled is not rl:
                source = "rl_inference+heuristic_guard"
            return reconciled, source
        except Exception as exc_rl:
            try:
                return _moderator()
            except Exception as exc_mod:
                return (
                    _heuristic_classify(content, author_display),
                    f"heuristic_fallback:rl_failed:{exc_rl}|moderator_failed:{exc_mod}",
                )

    # auto
    if use_local:
        try:
            rl = _rl_classify(content, author_display)
            heur = _heuristic_classify(content, author_display)
            reconciled = _reconcile(rl, heur, content)
            source = "rl_inference" if reconciled is rl else "rl_inference+heuristic_guard"
            return reconciled, source
        except Exception:
            pass
    if _has_openai_key():
        try:
            return _moderator()
        except Exception as exc:
            return _heuristic_classify(content, author_display), f"heuristic_fallback:moderator_failed:{exc}"
    return _heuristic_classify(content, author_display), "heuristic_auto"
