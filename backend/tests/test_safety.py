"""Safety suite (Section 17.1): every must_be_emergency case returns urgency = emergency, in every language."""
from collections import Counter

import pytest

from app import pipeline
from conftest import load_suite

SUITE = load_suite()
EMERGENCIES = [c for c in SUITE if c["must_be_emergency"]]


@pytest.mark.parametrize("case", EMERGENCIES, ids=[c["id"] for c in EMERGENCIES])
def test_no_missed_emergency(case):
    r = pipeline.analyze(None, case["text"])
    assert r["urgency"] == "emergency", f"missed emergency: {case['text']!r} -> {r['urgency']} {r['slots']}"
    # The first screen must put Call 112 first: the emergency screen, or the child screen.
    assert r["next_screen"] in ("emergency", "child")


@pytest.mark.parametrize("case", SUITE, ids=[c["id"] for c in SUITE])
def test_language_detected(case):
    assert pipeline.analyze(None, case["text"])["detected_lang"] == case["lang"]


@pytest.mark.parametrize("case", SUITE, ids=[c["id"] for c in SUITE])
def test_expected_situation(case):
    r = pipeline.analyze(None, case["text"])
    got = "child" if r["child_or_infant"] else ("out_of_scope" if r["out_of_scope"] else r["situation"]["id"])
    assert got == case["expect"]


def test_every_language_is_covered():
    counts = Counter(c["lang"] for c in EMERGENCIES)
    for lang in ("en", "hi", "hinglish", "mr"):
        assert counts[lang] >= 15, f"safety suite needs more {lang} emergencies"


def test_over_triage_report():
    """Not a hard requirement (over-triage is the safe direction), but keep it visible."""
    non = [c for c in SUITE if not c["must_be_emergency"]]
    over = [c["id"] for c in non if pipeline.analyze(None, c["text"])["urgency"] == "emergency"]
    assert len(over) <= len(non) // 2, f"too many non-emergencies raised to emergency: {over}"


def test_model_can_raise_but_rules_floor_holds(monkeypatch):
    """A triage model that says 'home' can never lower an emergency found by the rules."""
    from app import models

    class LowballTriage:
        def predict(self, text, lang, slots):
            return {"urgency": "home", "scores": {"home": 1.0}, "harmful": None, "all_harmful": []}

    reg = dict(models.registry())
    reg["triage"] = LowballTriage()
    monkeypatch.setattr(pipeline, "registry", lambda: reg)
    r = pipeline.analyze(None, "he is unconscious and not breathing")
    assert r["urgency"] == "emergency"


def test_model_can_raise_urgency(monkeypatch):
    from app import models

    class CautiousTriage:
        def predict(self, text, lang, slots):
            return {"urgency": "emergency", "scores": {"emergency": 1.0}, "harmful": None, "all_harmful": []}

    reg = dict(models.registry())
    reg["triage"] = CautiousTriage()
    monkeypatch.setattr(pipeline, "registry", lambda: reg)
    r = pipeline.analyze(None, "small burn from the iron")
    assert r["urgency"] == "emergency"
