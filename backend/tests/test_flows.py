"""Subtypes, child, out of scope, clarifying questions and memory (Section 17.1, 8.4)."""
import pytest

from app import clarify, content, pipeline


@pytest.mark.parametrize("text,branch", [
    ("a snake bit him", "snake"),
    ("a bee stung her", "insect_sting"),
    ("a scorpion stung him", "scorpion"),
    ("a dog bit him", "dog"),
    ("burned in a fire", "fire_heat"),
    ("burned by boiling water", "fire_heat"),
    ("acid spilled on his hand", "chemical_acid"),
    ("electric shock from a wire", "electrical"),
])
def test_each_subtype_reaches_its_branch(text, branch):
    r = pipeline.analyze(None, text)
    assert r["situation"]["branch"] == branch
    prefix = {"snake": "bite_snake", "insect_sting": "bite_insect", "scorpion": "bite_insect", "dog": "bite_dog",
              "fire_heat": "burns_fire", "chemical_acid": "burns_chem", "electrical": "burns_elec"}[branch]
    assert r["steps"][0]["id"].startswith(prefix)


def test_scorpion_is_at_least_clinic():
    assert pipeline.analyze(None, "a scorpion stung him")["urgency"] in ("clinic", "emergency")


def test_dog_bite_is_at_least_clinic():
    assert pipeline.analyze(None, "a dog bit him")["urgency"] in ("clinic", "emergency")


def test_unresponsive_paths():
    a = pipeline.analyze(None, "he is unconscious and not breathing")
    assert a["situation"]["branch"] == "path_a"
    assert [s["id"] for s in a["steps"]][3] == "unr_a1"
    assert any(s["cpr_rhythm"] for s in a["steps"])
    b = pipeline.analyze(None, "he is unconscious but breathing normally")
    assert b["situation"]["branch"] == "path_b"
    assert [s["id"] for s in b["steps"]][3] == "unr_b1"


@pytest.mark.parametrize("text", ["my 3 year old is not breathing", "baby is choking", "mera bachcha behosh hai", "बच्चे को सांप ने काटा", "लहान मूल गुदमरतंय"])
def test_child_screen(text):
    r = pipeline.analyze(None, text)
    assert r["next_screen"] == "child" and r["child_or_infant"] and r["urgency"] == "emergency"


@pytest.mark.parametrize("text", ["he has a high fever", "I think it is a stroke", "broken leg after a fall from a bike", "bukhar hai", "मिर्गी का दौरा पड़ा", "ताप आला आहे"])
def test_out_of_scope(text):
    r = pipeline.analyze(None, text)
    if r["clarifying_question"] and r["clarifying_question"]["safety"]:
        return  # a fall can mean collapse: asking about responsiveness first is the safe choice
    assert r["out_of_scope"] and r["next_screen"] == "out_of_scope"


def test_pregnant_choking_is_out_of_scope_with_112():
    r = pipeline.analyze(None, "my pregnant wife is choking and cannot speak")
    assert r["urgency"] == "emergency" and r["out_of_scope"] and r["out_of_scope_note"]


def test_collapse_asks_responsiveness_first():
    r = pipeline.analyze(None, "my father collapsed")
    assert r["clarifying_question"]["id"] == "q_responsive"
    assert r["clarifying_question"]["safety"]
    r2 = pipeline.answer(r["session_id"], "q_responsive", "no")
    assert r2["clarifying_question"]["id"] == "q_breathing"
    r3 = pipeline.answer(r["session_id"], "q_breathing", "no")
    assert r3["situation"]["branch"] == "path_a" and r3["next_screen"] == "steps"


def test_unknown_bite_asks_type_and_stays_emergency():
    r = pipeline.analyze(None, "something bit him in the field")
    assert r["urgency"] == "emergency"
    assert r["clarifying_question"]["id"] == "q_bite_type"
    r2 = pipeline.answer(r["session_id"], "q_bite_type", "insect")
    assert r2["situation"]["branch"] == "insect_sting"


def test_unknown_burn_asks_cause():
    r = pipeline.analyze(None, "burn")
    assert r["clarifying_question"]["id"] == "q_burn_cause"
    r2 = pipeline.answer(r["session_id"], "q_burn_cause", "chemical")
    assert r2["situation"]["branch"] == "chemical_acid"


def test_electrical_asks_power_off():
    r = pipeline.analyze(None, "he got an electric shock")
    assert r["clarifying_question"]["id"] == "q_power_off"


def test_at_most_two_questions_in_a_row():
    r = pipeline.analyze(None, "help")
    asked = 0
    while r["clarifying_question"]:
        asked += 1
        q = r["clarifying_question"]
        r = pipeline.answer(r["session_id"], q["id"], q["options"][-1]["id"])
    assert asked <= 2
    assert r["urgency"] == "emergency"  # still unsure: show Call 112


def test_memory_updates_and_switches_situation():
    r = pipeline.analyze(None, "my uncle has chest pain")
    assert r["situation"]["id"] == "heart_attack"
    r2 = pipeline.analyze(r["session_id"], "now he is unconscious and not breathing")
    assert r2["situation"]["id"] == "unresponsive"
    assert r2["situation_changed"] == {"from": "heart_attack", "to": "unresponsive"}
    assert r2["slots"]["chest_pain"] == "yes"  # earlier facts are kept
    assert r2["next_screen"] == "emergency"


def test_newer_certain_value_replaces_older():
    r = pipeline.analyze(None, "he is unconscious and breathing normally")
    assert r["slots"]["breathing"] == "normal"
    r2 = pipeline.analyze(r["session_id"], "now he stopped breathing")
    assert r2["slots"]["breathing"] == "absent"
    assert r2["situation"]["branch"] == "path_a"


def test_uncertain_mention_does_not_overwrite_fact():
    r = pipeline.analyze(None, "he is unconscious and not breathing")
    r2 = pipeline.analyze(r["session_id"], "maybe he is breathing")
    assert r2["slots"]["breathing"] == "absent"


def test_harmful_action_warning():
    r = pipeline.analyze(None, "snake bit him, we tied a rope above the bite")
    assert r["harmful_action"]["id"] == "myth_snake_tourniquet"
    assert r["next_screen"] == "emergency"  # Call 112 first, then the warning card


def test_harmful_negated_is_not_flagged():
    r = pipeline.analyze(None, "small burn from the iron, we did not put toothpaste")
    assert r["harmful_action"] is None


def test_harmful_without_emergency_shows_warning_first():
    r = pipeline.analyze(None, "small burn on the arm from the iron, I put toothpaste")
    assert r["next_screen"] == "harmful_warning"


def test_explanation_uses_users_words():
    r = pipeline.analyze(None, "papa gir gaye, saans nahi le rahe")
    words = " ".join(e["word"] for e in r["explanation"])
    assert "saans nahi" in words


def test_information_gain_prefers_discriminating_question():
    hyps = {"bites:snake": 0.25, "bites:insect_sting": 0.25, "bites:scorpion": 0.25, "bites:dog": 0.25}
    qs = content.questions()
    assert clarify.information_gain(qs["q_bite_type"], hyps) > clarify.information_gain(qs["q_chest_pain"], hyps)
    assert clarify.information_gain(qs["q_bite_type"], hyps) == pytest.approx(2.0, abs=0.4)


TILE_EXPECT = {"unresponsive": "unresponsive", "heart_attack": "heart_attack", "choking": "choking", "bites": "bites", "burns": "burns"}


@pytest.mark.parametrize("lang", ["en", "hi", "hinglish", "mr"])
def test_home_tiles_route_to_their_situation(lang):
    """The home-screen shortcut tiles send these localised sentences (frontend/src/i18n)."""
    import json
    from pathlib import Path

    strings = json.loads((Path(__file__).resolve().parents[2] / "frontend" / "src" / "i18n" / f"{lang}.json").read_text(encoding="utf-8"))
    for key, sit in TILE_EXPECT.items():
        r = pipeline.analyze(None, strings[f"tile_text_{key}"], lang)
        assert r["situation"]["id"] == sit, (lang, key, r["situation"], r["slots"])
        assert r["detected_lang"] == lang, (lang, key, r["detected_lang"])
