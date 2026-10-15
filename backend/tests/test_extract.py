"""F1 extraction (Section 8.3)."""
import pytest

from app.extract import extract
from app.normalize import normalize


def test_devanagari_digits_normalised():
    assert normalize("६० वर्षांचे").text.startswith("60")


@pytest.mark.parametrize("lang,text,group", [
    ("en", "my 60 year old father", "adult"),
    ("en", "a 7 year old boy", "child"),
    ("en", "8 months old", "infant"),
    ("hinglish", "60 saal ke papa", "adult"),
    ("mr", "६० वर्षांचे आजोबा", "adult"),
    ("hi", "5 साल का बच्चा", "child"),
    ("en", "my baby", "infant"),
])
def test_age_group(lang, text, group):
    assert extract(text, lang).slots.get("age_group") == group


@pytest.mark.parametrize("lang,text,slot,value", [
    ("en", "a snake bit him", "bite_type", "snake"),
    ("en", "stung by a scorpion", "bite_type", "scorpion"),
    ("en", "a wasp stung her", "bite_type", "insect_sting"),
    ("en", "a stray dog bit him", "bite_type", "dog"),
    ("en", "a monkey bit her", "bite_type", "other_mammal"),
    ("hinglish", "saap ne kaat liya", "bite_type", "snake"),
    ("hinglish", "bichhu ne dank mara", "bite_type", "scorpion"),
    ("hi", "कुत्ते ने काटा", "bite_type", "dog"),
    ("mr", "विंचू चावला", "bite_type", "scorpion"),
    ("en", "burned by boiling water", "burn_cause", "hot_liquid_steam"),
    ("en", "burned with acid", "burn_cause", "chemical_acid"),
    ("en", "electric shock", "burn_cause", "electrical"),
    ("hinglish", "current laga", "burn_cause", "electrical"),
    ("hi", "आग से जल गया", "burn_cause", "fire_heat"),
    ("mr", "गरम पाण्याने भाजलं", "burn_cause", "hot_liquid_steam"),
    ("en", "burn on the face", "burn_area", "eyes_or_face"),
    ("en", "burn bigger than his palm", "burn_area", "large"),
    ("en", "chest pain", "chest_pain", "yes"),
    ("en", "he is unresponsive", "responsive", "no"),
    ("en", "she is gasping", "breathing", "abnormal"),
    ("en", "power is off now", "power_off", "yes"),
])
def test_slots(lang, text, slot, value):
    assert extract(text, lang).slots.get(slot) == value


def test_typo_tolerance():
    assert extract("he is unconcious", "en").slots.get("responsive") == "no"
    assert extract("he is not breatheing", "en").slots.get("breathing") == "absent"


def test_hinglish_spellings():
    for t in ["behosh ho gaye", "behos ho gaya"]:
        assert extract(t, "hinglish").slots.get("responsive") == "no", t


def test_time_since():
    assert extract("bitten about 20 minutes ago", "en").slots.get("time_since") == "20 minutes"
    assert extract("10 minat pehle", "hinglish").slots.get("time_since") == "10 minat"


def test_actions_taken():
    assert "Called 112" in extract("I called an ambulance", "en").actions


def test_evidence_keeps_original_spelling():
    e = extract("Papa Gir Gaye, SAANS nahi", "hinglish")
    words = [ev.text for ev in e.evidence]
    assert any(w.startswith("SAANS") for w in words)
