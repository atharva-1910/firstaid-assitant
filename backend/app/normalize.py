"""Step [1] of the pipeline: Unicode clean-up, digit normalisation and tokenisation.

The normalised string keeps a map back to the original text, so the explanation
(F4) can highlight the user's own words exactly as they typed them.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

DEVANAGARI_DIGITS = {chr(0x0966 + i): str(i) for i in range(10)}
CHANDRABINDU = "ँ"
ANUSVARA = "ं"
NUKTA = "़"
ZW = {"​", "‌", "‍", "﻿"}
# Curly apostrophes are common on phones ("can’t")
APOSTROPHES = {"’": "'", "‘": "'", "`": "'", "ʼ": "'"}

# A word is Latin letters/digits/apostrophes, or a run of Devanagari letters and marks.
_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?|[ऀ-ॣ०-ॿ‌‍]+|[,.;:!?|।॥]")
BREAK_CHARS = set(",.;:!?|।॥")


@dataclass
class Token:
    text: str
    start: int  # index in the normalised string
    end: int
    is_break: bool = False


@dataclass
class Normalized:
    original: str
    text: str
    index_map: list[int]  # normalised char index -> original char index

    def original_span(self, start: int, end: int) -> tuple[int, int]:
        if not self.index_map:
            return (0, 0)
        o_start = self.index_map[min(start, len(self.index_map) - 1)]
        o_end = self.index_map[min(end - 1, len(self.index_map) - 1)] + 1
        return o_start, o_end

    def original_text(self, start: int, end: int) -> str:
        s, e = self.original_span(start, end)
        return self.original[s:e]


def normalize(text: str) -> Normalized:
    out: list[str] = []
    imap: list[int] = []
    for i, ch in enumerate(text):
        # NFKC per character keeps the index map simple and folds full-width forms.
        for c in unicodedata.normalize("NFKC", ch):
            if c in ZW:
                continue
            if c in DEVANAGARI_DIGITS:
                c = DEVANAGARI_DIGITS[c]
            elif c == CHANDRABINDU:
                c = ANUSVARA
            elif c == NUKTA:
                continue
            elif c in APOSTROPHES:
                c = APOSTROPHES[c]
            elif c.isspace():
                c = " "
            else:
                c = c.lower()
            out.append(c)
            imap.append(i)
    # Decompose precomposed nukta letters (e.g. U+095C) that NFKC keeps as one char.
    joined = "".join(out)
    if any("क़" <= c <= "य़" for c in joined):
        out2: list[str] = []
        imap2: list[int] = []
        for c, i in zip(out, imap):
            if "क़" <= c <= "य़":
                for d in unicodedata.normalize("NFD", c):
                    if d != NUKTA:
                        out2.append(d)
                        imap2.append(i)
            else:
                out2.append(c)
                imap2.append(i)
        out, imap = out2, imap2
    return Normalized(original=text, text="".join(out), index_map=imap)


def tokenize(norm: Normalized) -> list[Token]:
    toks: list[Token] = []
    for m in _TOKEN_RE.finditer(norm.text):
        t = m.group(0)
        toks.append(Token(t, m.start(), m.end(), is_break=t in BREAK_CHARS))
    return toks


def normalize_term(term: str) -> str:
    """Normalise a lexicon term the same way as user text."""
    return normalize(term).text.strip()
