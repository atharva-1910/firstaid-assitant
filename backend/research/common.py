"""Shared pieces for the research experiments (docs/research/README.md).

Everything here runs on a laptop CPU with scikit-learn. Transformer runs live in
training/05_research_transformers.ipynb (Colab) and reuse the same data, splits and metrics.
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parent.parent
REPO = BACKEND.parent
DATA = BACKEND / "data" / "queries"
OUT = REPO / "docs" / "research"
FIG = OUT / "figures"
sys.path.insert(0, str(BACKEND))

LANGS = ["en", "hi", "hinglish", "mr"]
LANG_NAMES = {"en": "English", "hi": "Hindi", "hinglish": "Hinglish", "mr": "Marathi"}
SITUATIONS = ["unresponsive", "heart_attack", "choking", "bites", "burns", "out_of_scope"]
SEED = 13


def jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def write_json(name: str, obj) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


# ------------------------------------------------------------------ data

def train_rows() -> list[dict]:
    return jsonl(DATA / "train.jsonl")


def dev_rows() -> list[dict]:
    return jsonl(DATA / "dev.jsonl")


def test_rows() -> list[dict]:
    """The hand-written test set (Section 10). Empty until the language owners write it."""
    p = DATA / "test.jsonl"
    return jsonl(p) if p.exists() and p.read_text(encoding="utf-8").strip() else []


def safety_rows() -> list[dict]:
    """Safety suite as evaluation rows: situation from `expect` (child counts as out of scope),
    urgency known only as emergency / not emergency."""
    out = []
    for r in jsonl(BACKEND / "tests" / "safety_suite.jsonl"):
        sit = r.get("expect")
        sit = "out_of_scope" if sit in ("child", "out_of_scope") else sit
        out.append({**r, "situation": sit if sit in SITUATIONS else None, "emergency": bool(r["must_be_emergency"])})
    return out


def probe_rows() -> list[dict]:
    """100 short, misspelt, code-mixed messages. Situation/urgency labels are silver (labelled by Claude)."""
    return jsonl(DATA / "probe_labelled.jsonl")


def is_emergency(row: dict) -> bool | None:
    if "emergency" in row:
        return row["emergency"]
    u = row.get("urgency")
    return None if u is None else u == "emergency"


EVAL_SETS = {
    "dev (template)": dev_rows,
    "safety suite (team-written)": safety_rows,
    "probe (machine-drafted, silver labels)": probe_rows,
}


def eval_sets() -> dict[str, list[dict]]:
    sets = {k: f() for k, f in EVAL_SETS.items()}
    t = test_rows()
    if t:
        sets = {"test (hand-written)": t, **sets}
    return sets


# ------------------------------------------------------------------ rules (the app's own pipeline, stub mode)

@lru_cache(maxsize=None)
def _pipeline():
    os.environ.setdefault("MODEL_MODE", "stub")
    from app import pipeline
    from app.memory import store

    return pipeline, store


def rules_predict(text: str) -> dict:
    pipeline, store = _pipeline()
    store.clear()
    r = pipeline.analyze(None, text)
    sit = r["situation"]["id"]
    if r.get("child_or_infant") or r.get("out_of_scope") or sit not in SITUATIONS:
        sit = "out_of_scope"
    return {"situation": sit, "urgency": r["urgency"], "emergency": r["urgency"] == "emergency"}


def rules_predict_at(commit: str, texts: list[str]) -> list[dict]:
    """The rules as they were at an older commit (for example before the probe-driven lexicon fixes)."""
    work = Path("/tmp") / f"firstaid-{commit}"
    if not work.exists():
        subprocess.run(["git", "-C", str(REPO), "worktree", "add", "--detach", str(work), commit], check=True, capture_output=True)
    code = (
        "import json,sys,os;os.environ['MODEL_MODE']='stub';sys.path.insert(0,'backend');"
        "from app import pipeline;from app.memory import store\n"
        "out=[]\n"
        "for t in json.load(sys.stdin):\n"
        "  store.clear();r=pipeline.analyze(None,t);s=r['situation']['id']\n"
        f"  s='out_of_scope' if r.get('child_or_infant') or r.get('out_of_scope') or s not in {SITUATIONS!r} else s\n"
        "  out.append({'situation':s,'urgency':r['urgency'],'emergency':r['urgency']=='emergency'})\n"
        "print(json.dumps(out))"
    )
    res = subprocess.run([sys.executable, "-c", code], cwd=work, input=json.dumps(texts), capture_output=True, text=True, check=True)
    return json.loads(res.stdout)


# ------------------------------------------------------------------ classical models

def make_model(kind: str, C: float = 10.0):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import ComplementNB
    from sklearn.pipeline import FeatureUnion, Pipeline

    word = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True, min_df=1, token_pattern=r"(?u)\b\w+\b")
    char = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=1)
    lr = LogisticRegression(C=C, max_iter=3000)
    if kind == "word":
        return Pipeline([("tfidf", word), ("clf", lr)])
    if kind == "char":
        return Pipeline([("tfidf", char), ("clf", lr)])
    if kind == "word+char":
        return Pipeline([("tfidf", FeatureUnion([("w", word), ("c", char)])), ("clf", lr)])
    if kind == "nb":
        return Pipeline([("tfidf", word), ("clf", ComplementNB(alpha=0.3))])
    raise ValueError(kind)


MODEL_LABELS = {
    "nb": "TF-IDF words + Naive Bayes",
    "word": "TF-IDF words (1-2) + LR",
    "char": "TF-IDF chars (2-5) + LR",
    "word+char": "TF-IDF words + chars + LR",
}


def fit(kind: str, rows: list[dict], target: str):
    xs = [r["text"] for r in rows if r.get(target)]
    ys = [r[target] for r in rows if r.get(target)]
    m = make_model(kind)
    m.fit(xs, ys)
    return m


# ------------------------------------------------------------------ metrics

def bootstrap_ci(values: list[float], n: int = 1000, seed: int = SEED) -> tuple[float, float, float]:
    """Mean and 95% percentile bootstrap interval of per-item scores (0/1)."""
    if not values:
        return (float("nan"),) * 3
    a = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = a[rng.integers(0, len(a), size=(n, len(a)))].mean(axis=1)
    return float(a.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def fmt_ci(t: tuple[float, float, float], digits: int = 2) -> str:
    m, lo, hi = t
    if m != m:
        return "–"
    return f"{m:.{digits}f} [{lo:.{digits}f}–{hi:.{digits}f}]"


def macro_f1(gold: list[str], pred: list[str], labels: list[str] = SITUATIONS) -> float:
    from sklearn.metrics import f1_score

    present = [l for l in labels if l in gold]
    return float(f1_score(gold, pred, labels=present, average="macro", zero_division=0)) if present else float("nan")


def by_lang(rows: list[dict]) -> dict[str, list[int]]:
    idx = defaultdict(list)
    for i, r in enumerate(rows):
        idx[r["lang"]].append(i)
    return idx


def seed_all(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)


def md_table(header: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)
