"""Content checks (Section 13.1 and 17.1): schema, sources, no invented text."""
import copy

import pytest

from app import config, content, pipeline
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


def test_step_images_exist_and_are_credited():
    steps_dir = config.REPO_DIR / "frontend" / "public" / "steps"
    found = 0
    for rec in content.situations().values():
        for branch in rec["branches"].values():
            for s in branch["steps"]:
                img = s.get("image")
                if not img:
                    continue
                found += 1
                assert (steps_dir / img["file"]).is_file(), img["file"]
                assert img["author"] and img["license"]
                # Either an openly licensed Commons file, or the team's own CC0 drawing with its SVG source in the repo.
                if not img["source_url"].startswith("https://commons.wikimedia.org/"):
                    assert img["license"] == "CC0 1.0", s["id"]
                    svg = config.REPO_DIR / "docs" / "illustrations" / img["file"].replace(".webp", ".svg")
                    assert svg.is_file(), svg
                for lang in LANGS:
                    assert img["alt"][lang].strip(), (s["id"], lang)
    assert found >= 14


def test_api_returns_step_image():
    r = pipeline.analyze(None, "my father collapsed and is not breathing")
    imgs = {s["id"]: s["image"] for s in r["steps"] if s["image"]}
    assert imgs["unr_a3"]["src"] == "/steps/unr_a3.webp" and imgs["unr_a3"]["license"]


def test_step_aids_only_time_what_the_step_says():
    """A timer must not invent a duration: its length has to appear in the step's own English text."""
    steps_dir = config.REPO_DIR / "frontend" / "public" / "steps"
    kinds = set()
    for rec in content.situations().values():
        for branch in rec["branches"].values():
            for s in branch["steps"]:
                aid = s.get("aid")
                if not aid:
                    continue
                kinds.add(aid["kind"])
                text = s["text"]["en"].lower()
                if aid["kind"] == "timer":
                    secs = aid["seconds"]
                    said = f"{secs // 60} minutes" if secs >= 60 else f"{secs} seconds"
                    assert said in text, (s["id"], said)
                if aid["kind"] == "stopwatch":
                    assert "until" in text, s["id"]
                if aid["kind"] == "cycle":
                    for p in aid["phases"]:
                        assert f"{p['count']} {p['key'].replace('_', ' ')}" in text, (s["id"], p["key"])
                        if p.get("image"):
                            assert (steps_dir / p["image"]).is_file(), p["image"]
                if aid["kind"] == "note_time":
                    assert "time" in text, s["id"]
    assert kinds == {"timer", "stopwatch", "cycle", "note_time"}


def test_api_returns_step_aids():
    r = pipeline.analyze(None, "my hand got burned by hot oil")
    aids = {s["id"]: s["aid"] for s in r["steps"] if s.get("aid")}
    assert aids.get("burns_fire_s2") == {"kind": "timer", "seconds": 1200}
    view = pipeline.situation_view("choking", "en", None)
    cycle = next(s["aid"] for s in view["steps"] if s["id"] == "ch_s6")
    assert [p["key"] for p in cycle["phases"]] == ["back_blows", "abdominal_thrusts"]
    assert cycle["phases"][0]["image"] == "/steps/anim/ch_s4.svg"


def test_step_animations_exist_and_respect_reduced_motion():
    steps_dir = config.REPO_DIR / "frontend" / "public" / "steps"
    found = set()
    for rec in content.situations().values():
        for branch in rec["branches"].values():
            for s in branch["steps"]:
                a = s.get("animation")
                if not a:
                    continue
                found.add(s["id"])
                svg = (steps_dir / a["file"]).read_text(encoding="utf-8")
                assert "@keyframes" in svg and "prefers-reduced-motion" in svg, a["file"]
                assert a["license"] == "CC0 1.0" and not a["verified"]
                for lang in LANGS:
                    assert a["alt"][lang].strip(), (s["id"], lang)
    assert {"unr_a4", "ch_s4", "ch_s5"} <= found


def test_cpr_animation_runs_at_the_pacer_rate():
    svg = (config.REPO_DIR / "frontend" / "public" / "steps" / "anim" / "unr_a4.svg").read_text(encoding="utf-8")
    assert "0.5455s" in svg  # 60 / 110 per minute, the same rate as the CPR rhythm circle
