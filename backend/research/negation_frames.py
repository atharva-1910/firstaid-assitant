"""Diagnostic negation set (machine-drafted; language owners must check and extend it).

13 frames x 5 people per language. Each frame names the facts it states and their gold value:
a slot value, or "uncertain". Frames test plain negation, uncertainty, a cue far from its word,
and two facts in one sentence with and without a scope breaker ("but", "lekin", "पण").
"""
from __future__ import annotations

FRAMES = {
    # id: (kind, gold)
    "F01": ("affirmed", {"breathing": "normal"}),
    "F02": ("negated", {"breathing": "absent"}),
    "F03": ("uncertain", {"breathing": "uncertain"}),
    "F04": ("negated", {"responsive": "no"}),
    "F05": ("affirmed", {"responsive": "yes"}),
    "F06": ("affirmed", {"chest_pain": "yes"}),
    "F07": ("negated", {"chest_pain": "no"}),
    "F08": ("negated, long scope", {"chest_pain": "no"}),
    "F09": ("two facts, with breaker", {"breathing": "normal", "responsive": "no"}),
    "F10": ("two facts, negated first", {"responsive": "no", "breathing": "normal"}),
    "F11": ("two facts, negated second", {"breathing": "normal", "responsive": "no"}),
    "F12": ("negated, cue 2-3 words away", {"breathing": "absent"}),
    "F13": ("uncertain (\"not sure if\")", {"breathing": "uncertain"}),
}

PEOPLE = {
    "en": [("my father", "my father's"), ("my grandfather", "my grandfather's"), ("my uncle", "my uncle's"), ("my brother", "my brother's"), ("the old man", "the old man's")],
    "hi": [("पापा", "पापा के"), ("दादाजी", "दादाजी के"), ("चाचा", "चाचा के"), ("भैया", "भैया के"), ("अंकल", "अंकल के")],
    "hinglish": [("papa", "papa ke"), ("dadaji", "dadaji ke"), ("chacha", "chacha ke"), ("bhaiya", "bhaiya ke"), ("uncle", "uncle ke")],
    "mr": [("बाबा", "बाबांच्या"), ("आजोबा", "आजोबांच्या"), ("काका", "काकांच्या"), ("दादा", "दादांच्या"), ("मामा", "मामांच्या")],
}

TEXT = {
    "en": {
        "F01": "{p} is breathing", "F02": "{p} is not breathing", "F03": "I think {p} is not breathing",
        "F04": "{p} is not responding", "F05": "{p} is responding", "F06": "{p} has chest pain",
        "F07": "{p} has no chest pain", "F08": "{p} has no pain or pressure in the chest",
        "F09": "{p} is breathing but not responding", "F10": "{p} is not responding and is breathing",
        "F11": "{p} is breathing and is not responding", "F12": "{p} is not even breathing",
        "F13": "not sure if {p} is breathing",
    },
    "hi": {
        "F01": "{p} साँस ले रहे हैं", "F02": "{p} साँस नहीं ले रहे", "F03": "शायद {p} साँस नहीं ले रहे",
        "F04": "{p} जवाब नहीं दे रहे", "F05": "{p} जवाब दे रहे हैं", "F06": "{g} सीने में दर्द है",
        "F07": "{g} सीने में दर्द नहीं है", "F08": "{g} सीने में कोई दर्द या दबाव नहीं है",
        "F09": "{p} साँस ले रहे हैं लेकिन जवाब नहीं दे रहे", "F10": "{p} जवाब नहीं दे रहे और साँस ले रहे हैं",
        "F11": "{p} साँस ले रहे हैं और जवाब नहीं दे रहे", "F12": "{p} साँस बिल्कुल भी नहीं ले रहे",
        "F13": "पता नहीं {p} साँस ले रहे हैं या नहीं",
    },
    "hinglish": {
        "F01": "{p} saans le rahe hain", "F02": "{p} saans nahi le rahe", "F03": "shayad {p} saans nahi le rahe",
        "F04": "{p} jawab nahi de rahe", "F05": "{p} jawab de rahe hain", "F06": "{g} seene mein dard hai",
        "F07": "{g} seene mein dard nahi hai", "F08": "{g} seene mein koi dard ya pressure nahi hai",
        "F09": "{p} saans le rahe hain lekin jawab nahi de rahe", "F10": "{p} jawab nahi de rahe aur saans le rahe hain",
        "F11": "{p} saans le rahe hain aur jawab nahi de rahe", "F12": "{p} saans bilkul bhi nahi le rahe",
        "F13": "pata nahi {p} saans le rahe hain ya nahi",
    },
    "mr": {
        "F01": "{p} श्वास घेत आहेत", "F02": "{p} श्वास घेत नाहीत", "F03": "कदाचित {p} श्वास घेत नाहीत",
        "F04": "{p} प्रतिसाद देत नाहीत", "F05": "{p} प्रतिसाद देत आहेत", "F06": "{g} छातीत दुखत आहे",
        "F07": "{g} छातीत दुखत नाही", "F08": "{g} छातीत कोणतीही वेदना किंवा दाब नाही",
        "F09": "{p} श्वास घेत आहेत पण प्रतिसाद देत नाहीत", "F10": "{p} प्रतिसाद देत नाहीत आणि श्वास घेत आहेत",
        "F11": "{p} श्वास घेत आहेत आणि प्रतिसाद देत नाहीत", "F12": "{p} श्वास अजिबात घेत नाहीत",
        "F13": "{p} श्वास घेत आहेत की नाही माहीत नाही",
    },
}


def build() -> list[dict]:
    rows = []
    for lang, frames in TEXT.items():
        for fid, tmpl in frames.items():
            kind, gold = FRAMES[fid]
            for i, (p, g) in enumerate(PEOPLE[lang]):
                rows.append({"id": f"neg-{lang}-{fid}-{i}", "lang": lang, "frame": fid, "kind": kind,
                             "text": tmpl.format(p=p, g=g), "gold": gold, "written_by": "claude (draft; owner to check)"})
    return rows
