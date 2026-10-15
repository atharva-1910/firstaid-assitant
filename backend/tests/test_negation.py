"""F3 negation and uncertainty (Section 8.5 and 17.1)."""
import pytest

from app.extract import extract

NOT_BREATHING = [
    ("en", "he is not breathing"),
    ("en", "she isn't breathing"),
    ("en", "he can't breathe and is unconscious"),
    ("hi", "साँस नहीं ले रहे"),
    ("hi", "वो सांस नहीं ले रही है"),
    ("hinglish", "saans nahi le rahe"),
    ("hinglish", "sans nhi le raha"),
    ("mr", "श्वास घेत नाही"),
    ("mr", "ते श्वास घेत नाहीत"),
]


@pytest.mark.parametrize("lang,text", NOT_BREATHING)
def test_not_breathing_sets_absent(lang, text):
    assert extract(text, lang).slots.get("breathing") == "absent"


AFFIRMED = [
    ("en", "he is breathing"),
    ("hi", "सांस ले रहे हैं"),
    ("hinglish", "saans le rahe hain"),
    ("mr", "श्वास घेत आहेत"),
]


@pytest.mark.parametrize("lang,text", AFFIRMED)
def test_breathing_affirmed(lang, text):
    assert extract(text, lang).slots.get("breathing") == "normal"


UNCERTAIN = [
    ("en", "I think he is not breathing"),
    ("en", "not sure if she is breathing"),
    ("hi", "पता नहीं सांस ले रहे हैं या नहीं"),
    ("hinglish", "pata nahi saans le rahe hain ya nahi"),
    ("mr", "माहीत नाही श्वास घेत आहेत का"),
    ("mr", "कदाचित श्वास घेत नाहीत"),
]


@pytest.mark.parametrize("lang,text", UNCERTAIN)
def test_uncertain_breathing_is_not_a_fact(lang, text):
    e = extract(text, lang)
    assert "breathing" not in e.slots
    assert "breathing" in e.uncertain


def test_negation_does_not_cross_punctuation():
    e = extract("no, he is breathing", "en")
    assert e.slots.get("breathing") == "normal"


def test_negation_does_not_cross_but():
    e = extract("not responding but breathing", "en")
    assert e.slots.get("responsive") == "no"
    assert e.slots.get("breathing") == "normal"


def test_no_chest_pain():
    for lang, text in [("en", "no chest pain"), ("hinglish", "seene mein dard nahi hai"), ("hi", "सीने में दर्द नहीं है"), ("mr", "छातीत दुखत नाही")]:
        assert extract(text, lang).slots.get("chest_pain") == "no", text


def test_cannot_cough_is_weak():
    assert extract("he is choking and cannot cough", "en").slots.get("choking_signs") == "weak_or_silent"


def test_power_not_off():
    assert extract("power is not switched off yet", "en").slots.get("power_off") == "no"
