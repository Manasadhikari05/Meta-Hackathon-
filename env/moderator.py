"""
AI-powered content moderator — OpenAI backend.

The AI reads the post and decides approve/remove/escalate
with a reason, severity, confidence, and explanation.
Users then rate its decision 1-10.
"""

import json
import os
import uuid

from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL       = os.getenv("AI_MODEL", "gpt-4o-mini")
TIMEOUT        = float(os.getenv("AI_GRADER_TIMEOUT", "60"))

client = OpenAI(api_key=OPENAI_API_KEY)

VALID_DECISIONS  = {"approve", "remove", "escalate"}
VALID_REASONS    = {"clean", "spam", "hate_speech", "harassment",
                    "misinformation", "self_harm", "violence", "sexual_content"}
VALID_SEVERITIES = {"low", "medium", "high"}

SYSTEM_PROMPT = (
    "You are a content moderation AI for a social media platform. "
    "Read the post and respond with valid JSON only — no markdown, no extra text.\n\n"
    'Format: {"decision":"<approve|remove|escalate>","reason_code":"<clean|spam|hate_speech|'
    'harassment|misinformation|self_harm|violence|sexual_content>","severity":"<low|medium|high>",'
    '"confidence":<0.0-1.0>,"explanation":"<one sentence plain English>",'
    '"reasoning_steps":["<step1>","<step2>","<step3>","<step4>","<step5>"],'
    '"thinking_summary":"<1-2 sentence summary>",'
    '"detailed_reasoning":"<full chain-of-thought, 3-5 sentences showing complete analysis>"}'
    '\n\n'
    'Provide:\n'
    '- reasoning_steps: 5 ultra-short steps (3-7 words each)\n'
    '- thinking_summary: 1-2 sentence overview\n'
    '- detailed_reasoning: Full chain-of-thought (3-5 sentences) showing exactly how you analyze the content, what factors you consider, and why you reach the decision.'
)

def _build_user_prompt(content: str, platform: str) -> str:
    return (
        f'POST: "{content}"\n'
        f"PLATFORM: {platform}\n\n"
        "Pick exactly one DECISION:\n"
        '- "approve"  — safe, follows community guidelines\n'
        '- "remove"   — clearly violates guidelines\n'
        '- "escalate" — borderline; needs human review\n\n'
        "Pick REASON_CODE, SEVERITY (low/medium/high), CONFIDENCE (0.0-1.0), and a one-sentence EXPLANATION.\n"
        "Respond with JSON only."
    )


def moderate(content: str, platform: str = "social_media") -> dict:
    """
    Have the AI moderate a piece of user-submitted content via OpenAI.

    Returns a dict with: post_id, content, platform, decision, reason_code,
    severity, confidence, explanation, model.
    Raises on API error — callers should catch and return 503.
    """
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": _build_user_prompt(content.strip(), platform)},
        ],
        temperature=0.1,
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    raw    = response.choices[0].message.content or "{}"
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

    explanation = (result.get("explanation") or "").strip()
    reasoning_steps = result.get("reasoning_steps", [])
    thinking_summary = result.get("thinking_summary", "")
    detailed_reasoning = result.get("detailed_reasoning", "")
    # Ensure we have exactly 5 steps; pad or truncate as needed
    if not isinstance(reasoning_steps, list):
        reasoning_steps = []
    while len(reasoning_steps) < 5:
        reasoning_steps.append("Analyzing content...")
    reasoning_steps = reasoning_steps[:5]

    return {
        "post_id":     str(uuid.uuid4())[:8],
        "content":     content.strip(),
        "platform":    platform,
        "decision":    decision,
        "reason_code": reason,
        "severity":    severity,
        "confidence":  confidence,
        "explanation": explanation,
        "reasoning_steps": reasoning_steps,
        "thinking_summary": thinking_summary,
        "detailed_reasoning": detailed_reasoning,
        "model":       AI_MODEL,
    }
