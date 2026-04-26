"""Classify OCR-extracted meme text using the same RL/Qwen core as Discord
moderation, then attach a fine-grained tag from a fixed vocabulary.

The decision (approve / remove / escalate) and severity still come from the
project core (`server.discord_classifier.classify_discord_message`), so memes
go through the *same* moderation brain as live Discord chat. We add a `tag`
field on top — produced by a deterministic heuristic over the OCR text, with
a sensible fallback derived from the model's `reason_code`.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from server.discord_classifier import classify_discord_message


# --- OCR text normalization -------------------------------------------------
# Memes often have OCR errors that wreck simple regexes. We do a small,
# *conservative* clean-up so contractions like "I'll" survive even when the
# OCR engine misreads them as "Il", "II", or "I1l".

_SMART_QUOTES = {
    "\u2018": "'", "\u2019": "'", "\u201A": "'", "\u201B": "'",
    "\u201C": '"', "\u201D": '"', "\u201E": '"', "\u201F": '"',
    "\u2032": "'", "\u2033": '"',
}

# OCR commonly merges "I'll" into one of these tokens.
_OCR_ILL_TOKEN = r"(?:I[Il1]+|Ill|I1l|II)"
# Verbs that signal a threat — used to scope the merge fix safely.
_THREAT_VERB = r"(?:kill|murder|stab|shoot|hate|end|destroy|fuck|beat)"

_OCR_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # "IIkill" / "Illkill" / "I1lkill" → "I'll kill"
    (re.compile(rf"\b{_OCR_ILL_TOKEN}({_THREAT_VERB})\b", re.I), r"I'll \1"),
    # "II kill" / "Ill kill" → "I'll kill"
    (re.compile(rf"\b{_OCR_ILL_TOKEN}\s+({_THREAT_VERB})\b", re.I), r"I'll \1"),
]


def _normalize_ocr(text: str) -> str:
    if not text:
        return text
    for src, repl in _SMART_QUOTES.items():
        text = text.replace(src, repl)
    for pat, repl in _OCR_PATTERNS:
        text = pat.sub(repl, text)
    return text

# Fine-grained vocabulary the user asked for. Order is *priority* — earlier
# entries override later ones when multiple patterns match.
TAG_VOCAB = [
    "Hate speech",
    "Threatening",
    "Bullying",
    "Harassment",
    "Abusive",
    "Toxic",
    "Offensive",
    "Aggressive",
    "Angry",
    "Harsh",
    "Sarcastic",
    "Passive-aggressive",
    "Frustrated",
    "Critical",
    "Negative",
    "Neutral",
    "Polite",
    "Friendly",
    "Positive",
    "Supportive",
]


# Heuristic tag detection. Patterns are evaluated in order; first match wins.
_TAG_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # --- High-severity ---
    (re.compile(r"\bn[i1]gg|\bf[a@]gg|\bk[i1]ke\b|\btr[a@]nn(?:y|ie)\b|\bch[i1]nk\b", re.I), "Hate speech"),
    (
        re.compile(
            r"\b(?:i\s*('?ll|will)\s*(?:kill|murder|stab|shoot)|"
            r"going\s+to\s+kill|"
            r"i'?ll\s+end\s+you|"
            r"kill\s+(?:you|him|her|them|yourself)|"
            r"\bbomb\b|\brape\b)",
            re.I,
        ),
        "Threatening",
    ),
    (re.compile(r"\bkys\b|\bkill\s+yourself\b|\bgo\s+(?:kill\s+yourself|die)\b", re.I), "Abusive"),
    (re.compile(r"\b(?:loser|garbage|worthless|pathetic|nobody\s+likes\s+you)\b", re.I), "Bullying"),
    (re.compile(r"\b(?:shut\s*up|you'?re\s+(?:a\s+)?(?:fool|moron|idiot|stupid|dumb))\b", re.I), "Harassment"),
    # --- Medium-severity ---
    (re.compile(r"\bfuck\b|\bshit\b|\bbitch\b|\bdick\b|\bcunt\b|\basshole\b|\bbastard\b", re.I), "Offensive"),
    (re.compile(r"\b(?:trash|garbage)\b", re.I), "Harsh"),
    (re.compile(r"\b(?:i\s+hate|hate\s+(?:you|them|him|her))\b", re.I), "Toxic"),
    (re.compile(r"\b(?:idiot|stupid|moron|dumb)\b", re.I), "Harsh"),
    (re.compile(r"\b(?:get\s+out|piss\s+off|go\s+away)\b", re.I), "Aggressive"),
    # All caps shouting (≥4 caps in a row, with at least one vowel) → Angry
    (re.compile(r"[A-Z]{4,}\b.*[!?]"), "Angry"),
    (re.compile(r"!{2,}|\?\?+|\b(?:wtf|omg|ugh)\b", re.I), "Angry"),
    # Sarcasm / passive-aggression
    (
        re.compile(
            r"(?:\byeah,?\s*right\b|\bsure,?\s*sure\b|\b/s\b|\bas\s+if\b|"
            r"\bwow,?\s*so\b|\bcongratulations\b.*\bgenius\b|\bbig\s+brain\b)",
            re.I,
        ),
        "Sarcastic",
    ),
    (re.compile(r"\bWHATEVER\b|\bsigh\b|\bfine\.\s*$|\bk\.\s*$|\bok\.\s*$", re.I), "Passive-aggressive"),
    # --- Low-severity ---
    (re.compile(r"\b(?:disagree|wrong|inaccurate|incorrect|misleading|fact[- ]check)\b", re.I), "Critical"),
    (re.compile(r"\bsuicid|\bself[-\s]?harm\b|\bso\s+tired\b|\bcan'?t\s+do\s+this\b", re.I), "Frustrated"),
    # --- Positive end ---
    (re.compile(r"\b(?:thanks|thank\s*you|please|kindly|appreciated|sorry)\b", re.I), "Polite"),
    (
        re.compile(
            r"\b(?:i\s+(?:got\s+you|am\s+here)|with\s+you|we'?ve\s+got\s+you|"
            r"keep\s+going|you\s+got\s+this|stay\s+strong)\b",
            re.I,
        ),
        "Supportive",
    ),
    (re.compile(r"\b(?:hi|hello|hey|gm|good\s+(?:morning|evening|night)|howdy|yo)\b", re.I), "Friendly"),
    (re.compile(r"\b(?:love|great|awesome|wonderful|amazing|happy|enjoying|nice|cool|lit)\b", re.I), "Positive"),
]


def _heuristic_tag(text: str) -> str | None:
    if not text:
        return None
    for pat, tag in _TAG_PATTERNS:
        if pat.search(text):
            return tag
    return None


def _tag_from_decision(decision: str, reason_code: str) -> str:
    rc = (reason_code or "").lower()
    decision = (decision or "").lower()
    mapping = {
        "hate_speech": "Hate speech",
        "violence": "Threatening",
        "harassment": "Harassment",
        "self_harm": "Frustrated",
        "spam": "Negative",
        "sexual_content": "Offensive",
        "misinformation": "Critical",
    }
    if rc in mapping:
        return mapping[rc]
    if rc == "clean":
        return "Neutral" if decision == "approve" else "Critical"
    return "Neutral"


def classify_meme_text(text: str) -> Dict[str, Any]:
    """Route OCR-extracted text through the project core; attach a tag.

    Returns a dict combining the moderation result with `tag` and
    `classifier_source`.
    """
    if not text or not text.strip():
        return {
            "decision": "approve",
            "reason_code": "clean",
            "severity": "low",
            "confidence": 0.5,
            "explanation": "no readable text detected in image",
            "tag": "Neutral",
            "model": "no_text",
            "classifier_source": "skipped_no_text",
        }

    cleaned = _normalize_ocr(text)
    moderation, source = classify_discord_message(cleaned, "meme_uploader")
    tag = _heuristic_tag(cleaned) or _tag_from_decision(
        moderation.get("decision", "escalate"),
        moderation.get("reason_code", "clean"),
    )

    out: Dict[str, Any] = dict(moderation)
    out["tag"] = tag
    out["classifier_source"] = source
    if cleaned != text:
        out["normalized_text"] = cleaned
    return out
