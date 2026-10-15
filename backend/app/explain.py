"""Feature F4: explainable emergency alert (owner: Soham Ghodake).

Returns the user's own words that triggered the alert, for the "Why this alert?" link.
Rule-triggered alerts always name the rule's trigger words. In real mode the explainer
adds token attributions from the IndicBERT v2 triage model when no rule fired.
"""
from __future__ import annotations

from .models import registry


def explain(texts: list[str], langs: list[str], urgency: str, triggers: list[tuple[str, str]]) -> list[dict]:
    """Looks through the conversation, newest message first, for the trigger words."""
    if urgency != "emergency":
        return []
    explainer = registry()["explainer"]
    for text, lang in reversed(list(zip(texts, langs))):
        words = explainer.explain(text, lang, urgency, triggers)
        if words:
            return [{"word": w["word"], "start": w["start"], "end": w["end"], "weight": w.get("weight", 1.0), "text": text} for w in words]
    return []
