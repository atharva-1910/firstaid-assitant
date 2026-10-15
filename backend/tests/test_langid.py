"""Language identification (trained char n-gram model) and the cross-language safety net."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from app.extract import SIBLING, extract, extract_safe
from app.models.ngram_langid import WEIGHTS, NgramLanguageId
from app.safety_rules import evaluate

DATA = Path(__file__).resolve().parent.parent / "data" / "queries"
SUITE = [json.loads(l) for l in (Path(__file__).parent / "safety_suite.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture(scope="module")
def model() -> NgramLanguageId:
    assert WEIGHTS.exists(), "run scripts/train_langid.py"
    return NgramLanguageId()


def test_probe_accuracy_per_language(model):
    rows = [json.loads(l) for l in (DATA / "langid_probe.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    tot, ok = Counter(), Counter()
    for r in rows:
        tot[r["lang"]] += 1
        ok[r["lang"]] += model.detect(r["text"])["lang"] == r["lang"]
    for lang in ("en", "hi", "hinglish", "mr"):
        assert ok[lang] / tot[lang] >= 0.95, f"{lang}: {ok[lang]}/{tot[lang]}"


@pytest.mark.parametrize("text,lang", [
    ("dadaji ko current laga 10 minute pehle", "hinglish"),
    ("tatiya ne kaata", "hinglish"),
    ("लवकर सांगा", "mr"),
    ("help", "en"),
])
def test_cases_the_word_lists_missed(model, text, lang):
    assert model.detect(text)["lang"] == lang


def test_script_decides_first(model):
    assert model.detect("साँस")["lang"] in ("hi", "mr")
    assert model.detect("saans")["lang"] in ("en", "hinglish")
    assert model.detect("")["lang"] in ("en", "hinglish")


def _urgency(e):
    return evaluate(e.slots, e.flags, e.sits, e.uncertain).urgency


def test_safety_net_catches_emergencies_under_a_wrong_language_guess():
    emergencies = [c for c in SUITE if c["must_be_emergency"]]
    missed = [c["text"] for c in emergencies if _urgency(extract_safe(c["text"], SIBLING[c["lang"]])) != "emergency"]
    plain = [c["text"] for c in emergencies if _urgency(extract(c["text"], SIBLING[c["lang"]])) != "emergency"]
    assert len(missed) <= 2, missed
    assert len(missed) < len(plain)


def test_safety_net_adds_no_false_alarms():
    for c in SUITE:
        if not c["must_be_emergency"]:
            for lang in (c["lang"], SIBLING[c["lang"]]):
                assert _urgency(extract_safe(c["text"], lang)) != "emergency", (lang, c["text"])


def test_safety_net_does_not_reread_negated_words():
    e = extract_safe("वह बेहोश नहीं है, साँस ले रहा है", "hi")
    assert e.slots.get("responsive") != "no"
    assert e.slots.get("breathing") not in ("absent", "abnormal")


def test_safety_net_matches_plain_extraction_when_language_is_right():
    for c in SUITE:
        a, b = extract(c["text"], c["lang"]), extract_safe(c["text"], c["lang"])
        assert _urgency(a) == _urgency(b), c["text"]
