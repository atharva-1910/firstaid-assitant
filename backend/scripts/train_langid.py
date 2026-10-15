"""Train the character n-gram language identifier and compare it with the word-list rules.

    cd backend && python scripts/train_langid.py          # needs requirements-offline.txt

Training data: data/queries/train.jsonl plus every translated sentence in content/ and the
frontend UI strings. Evaluation: data/queries/dev.jsonl, tests/safety_suite.jsonl and
data/queries/langid_probe.jsonl (realistic, harder messages; never used for training).
Writes app/models/weights/langid_charngram.json.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.models.ngram_langid import WEIGHTS, NgramLanguageId, features  # noqa: E402
from app.models.stub import StubLanguageId  # noqa: E402

LANGS = ["en", "hi", "hinglish", "mr"]
I18N = {"en": "en", "hi": "hi", "hinglish": "hinglish", "mr": "mr"}


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def content_sentences() -> list[tuple[str, str]]:
    """Every {"en":..,"hi":..,"hinglish":..,"mr":..} value in the content files."""
    out: list[tuple[str, str]] = []

    def walk(o):
        if isinstance(o, dict):
            if all(k in o for k in LANGS):
                out.extend((o[k], k) for k in LANGS if isinstance(o[k], str) and o[k].strip())
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    content = BACKEND / "content"
    for f in sorted((content / "situations").glob("*.json")) + [content / "questions.json", content / "strings.json"]:
        walk(json.loads(f.read_text(encoding="utf-8")))
    for rec in jsonl(content / "myths.jsonl"):
        walk(rec)
    return out


def ui_sentences() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    i18n = BACKEND.parent / "frontend" / "src" / "i18n"

    def walk(o, lang):
        if isinstance(o, dict):
            for v in o.values():
                walk(v, lang)
        elif isinstance(o, str) and o.strip():
            out.append((o, lang))

    for lang, name in I18N.items():
        f = i18n / f"{name}.json"
        if f.exists():
            walk(json.loads(f.read_text(encoding="utf-8")), lang)
    return out


def accuracy(detect, rows: list[tuple[str, str]]) -> tuple[dict, list]:
    tot, ok, errors = Counter(), Counter(), []
    for text, gold in rows:
        pred = detect(text)["lang"]
        tot[gold] += 1
        ok[gold] += pred == gold
        if pred != gold:
            errors.append((gold, pred, text))
    per = {lang: (ok[lang], tot[lang]) for lang in LANGS if tot[lang]}
    return per, errors


def fmt(per: dict) -> str:
    cells = [f"{ok}/{n}" for ok, n in per.values()]
    total_ok = sum(ok for ok, _ in per.values())
    total = sum(n for _, n in per.values())
    return " | ".join(cells) + f" | **{total_ok / total:.3f}**"


def main() -> None:
    queries = BACKEND / "data" / "queries"
    train = [(q["text"], q["lang"]) for q in jsonl(queries / "train.jsonl")]
    train += content_sentences() + ui_sentences()
    # English UI and content strings are shared with the test-free English side; dedupe.
    train = list(dict.fromkeys(train))
    print("training sentences:", Counter(lang for _, lang in train))

    vec = TfidfVectorizer(analyzer=features, sublinear_tf=True, min_df=2, norm="l2", smooth_idf=True)
    X = vec.fit_transform([t for t, _ in train])
    y = [lang for _, lang in train]
    clf = LogisticRegression(C=10.0, max_iter=5000)
    clf.fit(X, y)

    vocab = vec.get_feature_names_out().tolist()
    weights = {
        "version": "charngram-1-4 tfidf+logreg v1",
        "classes": clf.classes_.tolist(),
        "vocab": vocab,
        "idf": [round(float(v), 5) for v in vec.idf_],
        "coef": [[round(float(v), 5) for v in row] for row in clf.coef_],
        "intercept": [round(float(v), 5) for v in np.atleast_1d(clf.intercept_)],
    }
    WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
    WEIGHTS.write_text(json.dumps(weights, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"features: {len(vocab)} · weights: {WEIGHTS.stat().st_size / 1024:.0f} KB")

    model, rules = NgramLanguageId(), StubLanguageId()
    sets = {
        "dev (templates)": [(q["text"], q["lang"]) for q in jsonl(queries / "dev.jsonl")],
        "safety suite": [(q["text"], q["lang"]) for q in jsonl(BACKEND / "tests" / "safety_suite.jsonl")],
        "probe (harder, hand-written)": [(q["text"], q["lang"]) for q in jsonl(queries / "langid_probe.jsonl")],
    }
    print("\n| Set | Method | en | hi | hinglish | mr | Overall |\n|---|---|---|---|---|---|---|")
    errs = {}
    for name, rows in sets.items():
        for label, m in (("word-list rules", rules), ("char n-gram model", model)):
            per, errors = accuracy(m.detect, rows)
            errs[(name, label)] = errors
            print(f"| {name} | {label} | {fmt(per)} |")
    for (name, label), errors in errs.items():
        if errors and "probe" in name:
            print(f"\n{label} errors on {name}:")
            for gold, pred, text in errors:
                print(f"  {gold} -> {pred}: {text}")


if __name__ == "__main__":
    main()
