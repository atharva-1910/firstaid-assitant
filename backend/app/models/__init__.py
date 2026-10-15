"""Model registry: picks stub or real implementations from MODEL_MODE (Section 12)."""
from __future__ import annotations

from functools import lru_cache

from .. import config
from .stub import (
    StubExplainer,
    StubLanguageId,
    StubRephraser,
    StubSituationClassifier,
    StubStepVerifier,
    StubTriage,
)

MODEL_NAMES = {
    "stub": {
        "langid": "stub: script ranges + Hinglish word list",
        "triage": "stub: lexicon keyword rules",
        "situation": "stub: keyword overlap",
        "verifier": "stub: always reject",
        "rephraser": "disabled",
        "explainer": "stub: rule trigger words",
    },
    "real": {
        "langid": "IndicLID (AI4Bharat, 2023)",
        "triage": "IndicBERT v2 (2023), fine-tuned",
        "situation": "BGE-M3 (2024)",
        "verifier": "mmBERT (2025), fine-tuned on IndicXNLI",
        "rephraser": "Gemma 3 4B (2025) via Ollama" if config.REPHRASE_ENABLED else "disabled",
        "explainer": "transformers-interpret on IndicBERT v2",
    },
}


@lru_cache(maxsize=1)
def registry() -> dict:
    if config.MODEL_MODE == "real":
        from .real import build

        return build()
    return {
        "langid": StubLanguageId(),
        "triage": StubTriage(),
        "situation": StubSituationClassifier(),
        "verifier": StubStepVerifier(),
        "rephraser": StubRephraser(),
        "explainer": StubExplainer(),
    }
