"""Trained language identification: character n-gram TF-IDF + logistic regression.

Spelling patterns ("-iye", "nahi", "आहे", "रहे") identify a language even when a message has
no marker words or is misspelt, which the word-list rules miss. Weights are trained offline by
scripts/train_langid.py and stored as JSON, so inference needs no extra libraries.

The script still decides first: Devanagari text can only be Hindi or Marathi, Latin text only
English or Hinglish. The classifier chooses within that pair.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from ..normalize import normalize

WEIGHTS = Path(__file__).resolve().parent / "weights" / "langid_charngram.json"
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
SCRIPT_LANGS = {"devanagari": ("hi", "mr"), "latin": ("en", "hinglish")}
_STRIP = re.compile(r"[0-9०-९.,!?;:\"'()\[\]{}।॥\-–—/\\*&%#@+=<>~`|_]+")
MIN_N, MAX_N = 1, 4


def features(text: str) -> list[str]:
    """Character n-grams inside each word, padded with spaces (shared with training)."""
    clean = _STRIP.sub(" ", normalize(text).text.lower())
    grams: list[str] = []
    for word in clean.split():
        w = f" {word} "
        for n in range(MIN_N, MAX_N + 1):
            if len(w) < n:
                break
            grams.extend(w[i : i + n] for i in range(len(w) - n + 1))
    return grams


def script_of(text: str) -> str:
    return "devanagari" if DEVANAGARI.search(text) else "latin"


class NgramLanguageId:
    def __init__(self, path: Path = WEIGHTS) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self.classes: list[str] = data["classes"]
        self.vocab: dict[str, int] = {g: i for i, g in enumerate(data["vocab"])}
        self.idf: list[float] = data["idf"]
        self.coef: list[list[float]] = data["coef"]  # [class][feature]
        self.intercept: list[float] = data["intercept"]
        self.version: str = data.get("version", "")

    def scores(self, text: str) -> dict[str, float]:
        """Probabilities over the two languages allowed by the text's script."""
        counts: dict[int, int] = {}
        for g in features(text):
            j = self.vocab.get(g)
            if j is not None:
                counts[j] = counts.get(j, 0) + 1
        x = {j: (1.0 + math.log(c)) * self.idf[j] for j, c in counts.items()}  # sublinear tf * idf
        norm = math.sqrt(sum(v * v for v in x.values())) or 1.0
        allowed = SCRIPT_LANGS[script_of(text)]
        logits = {}
        for k, lang in enumerate(self.classes):
            if lang in allowed:
                row = self.coef[k]
                logits[lang] = self.intercept[k] + sum(v * row[j] for j, v in x.items()) / norm
        top = max(logits.values())
        exp = {lang: math.exp(v - top) for lang, v in logits.items()}
        total = sum(exp.values())
        return {lang: e / total for lang, e in exp.items()}

    def detect(self, text: str) -> dict:
        script = script_of(text)
        if script == "devanagari":
            share = english_in_devanagari(text)
            if share is not None:
                return {"lang": "en", "script": script, "p": round(min(0.99, 0.55 + share), 4), "transliterated": True}
        probs = self.scores(text)
        lang = max(probs, key=probs.get)
        return {"lang": lang, "script": script, "p": round(probs[lang], 4)}


# English heard by a Hindi or Marathi speech recogniser comes back written in Devanagari
# ("माय फादर इज़ नॉट ब्रीदिंग"). These are English words, mostly function words, as such a
# recogniser spells them. Words that are also common Hindi or Marathi words are left out
# (इस, ही, दे, इन, हर, आई, मी, दी, ना, तो, and loanwords such as हेल्प, प्लीज़, अंकल), so a Hindi sentence with English loanwords such as
# "हार्ट अटैक" or "करंट" is not mistaken for English.
_EN_IN_DEVANAGARI = {
    "माय", "इज़", "नॉट", "द", "एंड", "शी", "हिज़", "इट", "इट्स", "ऑफ", "टू", "विद", "विथ", "हैज़", "हैव",
    "कैन", "कांट", "कान्ट", "प्लीज़", "व्हाट", "डू", "डोंट", "डज़", "एम", "आर", "वॉज़", "वाज़", "दिस", "दैट", "देयर",
    "समवन", "यू", "योर", "वेरी", "नाउ", "गॉट", "ऑन", "ऐट", "विल", "शुड", "हाउ", "आफ्टर", "बिकॉज़", "वी", "ही'ज़",
    "ब्रीदिंग", "रिस्पॉन्डिंग", "रेस्पॉन्डिंग", "कोलैप्स्ड", "कॉलेप्स्ड", "अनकॉन्शियस", "बिटन", "बर्न्ड", "चोकिंग",
    "फादर", "मदर", "ब्रदर", "सिस्टर", "हस्बैंड", "वाइफ",
}
_EN_LATIN = {"my", "is", "not", "the", "and", "he", "she", "his", "her", "it", "of", "to", "with", "has", "have", "can",
             "please", "what", "do", "am", "are", "was", "this", "that", "someone", "you", "your", "breathing", "help"}
_EN_DEV_NORM = {normalize(w).text for w in _EN_IN_DEVANAGARI}
_WORD = re.compile(r"[a-z']+|[ऀ-ॿ]+")


def english_in_devanagari(text: str) -> float | None:
    """Share of words that are English written in Devanagari (or English Latin words mixed in),
    when it is high enough to call the message English; otherwise None."""
    words = _WORD.findall(normalize(text).text)
    if len(words) < 2:
        return None
    hits = sum(1 for w in words if w in _EN_DEV_NORM or w in _EN_LATIN)
    share = hits / len(words)
    return share if hits >= 2 and share >= 0.4 else None
