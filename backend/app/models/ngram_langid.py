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
        probs = self.scores(text)
        lang = max(probs, key=probs.get)
        return {"lang": lang, "script": script_of(text), "p": round(probs[lang], 4)}
