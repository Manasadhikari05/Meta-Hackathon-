"""
AI-powered content moderator.

The AI is the agent here — it reads the post and decides approve/remove/escalate
with a reason, severity, confidence, and explanation. Users then rate its decision.
"""

import json
import os
import uuid

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL",        "http://localhost:11434")
AI_MODEL   = os.getenv("AI_GRADER_MODEL",   "llama3.2:latest")
TIMEOUT    = float(os.getenv("AI_GRADER_TIMEOUT", "60"))

VALID_DECISIONS  = {"approve", "remove", "escalate"}
VALID_REASONS    = {"clean", "spam", "hate_speech", "harassment",
                    "misinformation", "self_harm", "violence", "sexual_content"}
VALID_SEVERITIES = {"low", "medium", "high"}


def _build_prompt(content: str, platform: str) -> str:
    return f"""You are a content moderation AI for a social media platform. Read the post and decide how to handle it.

POST: "{content}"
PLATFORM: {platform}

Pick exactly one DECISION:
- "approve"   — content is safe and follows community guidelines
- "remove"    — content clearly violates guidelines and must be taken down
- "escalate"  — borderline content; send to human review

Pick exactly one REASON_CODE:
- "clean"          — no issues found
- "spam"           — promotional, repetitive, or scam content
- "hate_speech"    — attacks based on race, religion, gender, nationality, etc.
- "harassment"     — targeted insults or threats toward a specific person
- "misinformation" — false or deliberately misleading claims
- "self_harm"      — content promoting self-harm or suicide
- "violence"       — violent threats, instructions, or graphic depictions
- "sexual_content" — explicit sexual material

Pick SEVERITY: "low" | "medium" | "high"
Set CONFIDENCE between 0.0 (very unsure) and 1.0 (certain)
Write a short EXPLANATION (one sentence, plain English)

Respond with valid JSON only — no markdown, no extra text:
{{"decision": "...", "reason_code": "...", "severity": "...", "confidence": 0.0, "explanation": "..."}}"""


def moderate(content: str, platform: str = "social_media") -> dict:
    """
    Have the AI moderate a piece of user-submitted content.

    Returns a dict with: post_id, content, platform, decision, reason_code,
    severity, confidence, explanation, model.
    Raises on Ollama error — callers should catch and 503.
    """
    prompt = _build_prompt(content.strip(), platform)

    resp = httpx.post(
        f"{OLLAMA_URL}/api/chat",
        json={
            "model":    AI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream":   False,
            "format":   "json",
            "options":  {"temperature": 0.1, "num_predict": 200},
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()

    raw    = resp.json()["message"]["content"]
    result = json.loads(raw)

    decision = result.get("decision", "escalate")
    if decision not in VALID_DECISIONS:
        decision = "escalate"

    reason = result.get("reason_code", "clean")
    if reason not in VALID_REASONS:
        reason = "clean"

    severity = result.get("severity", "medium")
    if severity not in VALID_SEVERITIES:
        severity = "medium"

    confidence = float(result.get("confidence", 0.5))
    confidence = round(max(0.0, min(1.0, confidence)), 3)

    return {
        "post_id":     str(uuid.uuid4())[:8],
        "content":     content.strip(),
        "platform":    platform,
        "decision":    decision,
        "reason_code": reason,
        "severity":    severity,
        "confidence":  confidence,
        "explanation": (result.get("explanation") or "").strip(),
        "model":       AI_MODEL,
    }
