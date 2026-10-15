"""Model registry: picks stub or real implementations from MODEL_MODE (Section 12)."""
from __future__ import annotations

from functools import lru_cache

from .. import config
from .ngram_langid import WEIGHTS as LANGID_WEIGHTS
from .ngram_langid import NgramLanguageId
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
        "langid": "char n-gram TF-IDF + logistic regression (trained, scripts/train_langid.py)",
        "triage": "stub: lexicon keyword rules",
        "situation": "stub: keyword overlap",
        "verifier": "stub: always reject",
        "rephraser": "disabled",
        "explainer": "stub: rule trigger words",
    },
    "real": {
        "langid": "IndicLID (AI4Bharat, 2023), char n-gram model as fallback",
        "triage": "IndicBERT v2 (2023), fine-tuned",
        "situation": "BGE-M3 (2024)",
        "verifier": "mmBERT (2025), fine-tuned on IndicXNLI",
        "rephraser": "Gemma 3 4B (2025) via Ollama" if config.REPHRASE_ENABLED else "disabled",
        "explainer": "transformers-interpret on IndicBERT v2",
    },
}


def use_ngram_langid() -> bool:
    return config.LANGID != "rules" and LANGID_WEIGHTS.exists()


def langid_name() -> str:
    return MODEL_NAMES[config.MODEL_MODE]["langid"] if use_ngram_langid() else "rules: script ranges + word lists"


def default_langid():
    """The trained n-gram model when its weights exist; LANGID=rules forces the word-list rules."""
    return NgramLanguageId() if use_ngram_langid() else StubLanguageId()


@lru_cache(maxsize=1)
def registry() -> dict:
    if config.MODEL_MODE == "real":
        from .real import build

        return build()
    return {
        "langid": default_langid(),
        "triage": StubTriage(),
        "situation": StubSituationClassifier(),
        "verifier": StubStepVerifier(),
        "rephraser": StubRephraser(),
        "explainer": StubExplainer(),
    }
