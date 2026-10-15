"""Model interfaces from Section 12. Each has a stub (rule-based) and a real implementation."""
from __future__ import annotations

from typing import Protocol


class LanguageId(Protocol):
    def detect(self, text: str) -> dict:  # {"lang": "en|hi|hinglish|mr", "script": "latin|devanagari"}
        ...


class Triage(Protocol):
    def predict(self, text: str, lang: str, slots: dict) -> dict:
        """{"urgency": "emergency|clinic|home", "scores": {...}, "harmful": {...} | None}"""
        ...


class SituationClassifier(Protocol):
    def predict(self, text: str, lang: str) -> list[dict]:
        """[{"situation": "bites", "p": 0.82}, ...] including "out_of_scope", sorted by p."""
        ...


class StepVerifier(Protocol):
    def entails(self, verified: str, candidate: str, lang: str) -> bool:
        ...


class Rephraser(Protocol):
    def rephrase(self, step: str, lang: str, record: dict) -> str | None:
        ...


class Explainer(Protocol):
    def explain(self, text: str, lang: str, urgency: str) -> list[dict]:
        """[{"word": "...", "start": 0, "end": 5, "weight": 0.7}]"""
        ...


from ..urgency import URGENCY_ORDER, max_urgency  # noqa: F401  (re-exported)
