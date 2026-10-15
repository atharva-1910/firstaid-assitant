"""Content checks (Section 13.1 and 17.1): schema, sources, no invented text."""
import copy

import pytest

from app import content, pipeline
from app.config import LANGS, SITUATIONS


def test_all_records_validate():
    for sid in SITUATIONS:
        rec = content.situations()[sid]
        assert content.validate_record(rec) == [], sid


def test_every_step_has_a_source():
    for sid, rec in content.situations().items():
        for bkey, branch in rec["branches"].items():
            for s in branch["steps"]:
                assert s["source"].get("doc"), f"{sid}/{bkey}/{s['id']} has no source"


def test_schema_rejects_step_without_source_doc():
    rec = copy.deepcopy(content.situations()["burns"])
    del rec["branches"]["fire_heat"]["steps"][0]["source"]["doc"]
    assert content.validate_record(rec), "schema accepted a step with no source.doc"


def test_schema_rejects_broken_next_pointer():
    rec = copy.deepcopy(content.situations()["choking"])
    rec["branches"]["default"]["steps"][0]["next"] = "does_not_exist"
    assert content.validate_record(rec)


def test_records_are_adult_only():
    assert all(r["age_scope"] == "adult" for r in content.situations().values())


def test_questions_have_english_text():
    for q in content.questions().values():
        assert q["text"]["en"]
        assert all(o["label"]["en"] for o in q["options"])


def test_myths_have_reasons():
    for m in content.myths():
        assert m["reason"]["en"] and m["action"]["en"]
        assert m["patterns"].get("en")


def test_lexicons_load_for_every_language():
    from app import lexicon

    for lang in LANGS:
        lex = lexicon.get(lang)
        assert lex.entry_terms and lex.neg_terms and lex.unc_terms


@pytest.mark.parametrize("text", [
    "he is unconscious and not breathing", "my uncle has chest pain", "choking, cannot speak",
    "snake bite on the leg", "dog bite", "bee sting", "scorpion sting", "burn from boiling water",
    "acid on the hand", "electric shock", "papa behosh ho gaye", "पापा बेहोश हो गए", "बाबा बेशुद्ध आहेत",
])
def test_no_invented_text(text):
    known = content.all_step_texts()
    r = pipeline.analyze(None, text, "auto")
    for s in r["steps"]:
        assert s["text"] in known or s["rephrased"], f"step text not in content files: {s['text']!r}"


def test_missing_translation_falls_back_to_english_with_label():
    r = pipeline.analyze(None, "पापा बेहोश हो गए, साँस नहीं ले रहे")
    assert r["display_lang"] == "hi"
    assert r["steps"], "expected steps"
    for s in r["steps"]:
        if s["translation_pending"]:
            assert s["text"] == next(
                st["text"]["en"] for b in content.situations()["unresponsive"]["branches"].values() for st in b["steps"] if st["id"] == s["id"]
            )


def test_localized_fallback_rules():
    assert content.localized({"en": "Call 112.", "hi": ""}, "hi") == ("Call 112.", True)
    assert content.localized({"en": "Call 112.", "hi": "112 पर कॉल करें।"}, "hi") == ("112 पर कॉल करें।", False)
    assert content.localized({"en": "", "hi": ""}, "hi") == ("", False)
    assert content.localized({"en": "Call 112."}, "en") == ("Call 112.", False)
