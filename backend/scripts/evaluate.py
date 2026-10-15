"""Evaluation per language, safety measures first (Section 17.2).

    python scripts/evaluate.py                         # data/queries/test.jsonl (falls back to dev.jsonl)
    python scripts/evaluate.py --file data/queries/dev.jsonl --baselines
    python scripts/evaluate.py --out ../docs/evaluation_report.md

Runs the full pipeline (in the current MODEL_MODE) on every query, one fresh session each,
and reports, per language and with the gap against English:
  triage: missed-emergency rate, emergency recall / precision, urgency macro-F1
  situation: accuracy, macro-F1, subtype accuracy, out-of-scope F1
  F1 extraction: slot-level micro F1
Baselines (--baselines, needs scikit-learn): TF-IDF + logistic regression trained on train.jsonl.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import config, pipeline  # noqa: E402
from app.memory import store  # noqa: E402

LANGS = ["en", "hi", "hinglish", "mr"]
CLASSES = ["unresponsive", "heart_attack", "choking", "bites", "burns", "out_of_scope"]
SLOT_KEYS = ["responsive", "breathing", "chest_pain", "choking_signs", "bite_type", "allergy_signs", "burn_cause", "burn_area", "power_off", "age_group"]


def load(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def f1(tp: int, fp: int, fn: int) -> float:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return 2 * p * r / (p + r) if p + r else 0.0


def macro_f1(gold: list[str], pred: list[str], labels: list[str]) -> float:
    scores = []
    for c in labels:
        tp = sum(g == c and p == c for g, p in zip(gold, pred))
        fp = sum(g != c and p == c for g, p in zip(gold, pred))
        fn = sum(g == c and p != c for g, p in zip(gold, pred))
        if tp + fp + fn:
            scores.append(f1(tp, fp, fn))
    return sum(scores) / len(scores) if scores else 0.0


def predicted_subtype(r: dict) -> str | None:
    sid, branch = r["situation"]["id"], r["situation"]["branch"]
    if sid == "unresponsive":
        return branch
    if sid in ("bites", "burns"):
        return branch
    return None


def evaluate(rows: list[dict]) -> dict[str, dict]:
    by_lang: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for q in rows:
        store.clear()
        r = pipeline.analyze(None, q["text"])
        by_lang[q["lang"]].append((q, r))
    out = {}
    for lang, pairs in by_lang.items():
        m: dict[str, float] = {"n": len(pairs)}
        # Triage
        urg = [(q["urgency"], r["urgency"]) for q, r in pairs if q.get("urgency")]
        gold_em = [p for g, p in urg if g == "emergency"]
        m["missed_emergency_rate"] = sum(p != "emergency" for p in gold_em) / len(gold_em) if gold_em else 0.0
        tp = sum(g == "emergency" and p == "emergency" for g, p in urg)
        fp = sum(g != "emergency" and p == "emergency" for g, p in urg)
        fn = sum(g == "emergency" and p != "emergency" for g, p in urg)
        m["emergency_recall"] = tp / (tp + fn) if tp + fn else 0.0
        m["emergency_precision"] = tp / (tp + fp) if tp + fp else 0.0
        m["urgency_macro_f1"] = macro_f1([g for g, _ in urg], [p for _, p in urg], ["emergency", "clinic", "home"])
        # Situation
        gold = [q["situation"] for q, _ in pairs]
        pred = []
        for q, r in pairs:
            if r["child_or_infant"] or r["out_of_scope"]:
                pred.append("out_of_scope")
            else:
                pred.append(r["situation"]["id"])
        m["situation_accuracy"] = sum(g == p for g, p in zip(gold, pred)) / len(pairs)
        m["situation_macro_f1"] = macro_f1(gold, pred, CLASSES)
        sub = [(q["subtype"], predicted_subtype(r)) for q, r in pairs if q.get("subtype")]
        m["subtype_accuracy"] = sum(g == p for g, p in sub) / len(sub) if sub else 0.0
        tp = sum(g == "out_of_scope" and p == "out_of_scope" for g, p in zip(gold, pred))
        fp = sum(g != "out_of_scope" and p == "out_of_scope" for g, p in zip(gold, pred))
        fn = sum(g == "out_of_scope" and p != "out_of_scope" for g, p in zip(gold, pred))
        m["out_of_scope_f1"] = f1(tp, fp, fn)
        # F1 extraction (slot-level micro F1 over slot=value pairs)
        tp = fp = fn = 0
        for q, r in pairs:
            g = {(k, v) for k, v in q.get("slots", {}).items() if k in SLOT_KEYS}
            p = {(k, v) for k, v in r["slots"].items() if k in SLOT_KEYS}
            tp += len(g & p)
            fp += len(p - g)
            fn += len(g - p)
        m["slot_f1"] = f1(tp, fp, fn)
        out[lang] = m
    return out


SUBTYPE_SLOT_VALUE = {"snake": ("bite_type", "snake"), "insect_sting": ("bite_type", "insect_sting"), "scorpion": ("bite_type", "scorpion"),
                      "dog": ("bite_type", "dog"), "chemical_acid": ("burn_cause", "chemical_acid"), "electrical": ("burn_cause", "electrical"),
                      "path_a": ("breathing", "absent"), "path_b": ("breathing", "normal")}


def _simulated_answer(question: dict, q: dict) -> str:
    """Answers a clarifying question from the gold labels, as a truthful user would."""
    from app import content

    gold = dict(q.get("slots", {}))
    if q.get("subtype") in SUBTYPE_SLOT_VALUE:
        k, v = SUBTYPE_SLOT_VALUE[q["subtype"]]
        gold.setdefault(k, v)
    if q["situation"] == "unresponsive":
        gold.setdefault("responsive", "no")
    if q["situation"] == "heart_attack":
        gold.setdefault("chest_pain", "yes")
    full = content.questions()[question["id"]]
    for o in full["options"]:
        if o["set"] and all(gold.get(k) == v or (k == "breathing" and v == "abnormal" and gold.get(k) == "absent") for k, v in o["set"].items()):
            return o["id"]
    for o in full["options"]:
        if o["id"] in ("not_sure", "no"):
            return o["id"]
    return full["options"][-1]["id"]


def clarify_resolution(rows: list[dict]) -> dict[str, dict]:
    """F2: share of ambiguous queries (those that get a question) resolved within 2 questions."""
    out: dict[str, dict] = {}
    for q in rows:
        store.clear()
        r = pipeline.analyze(None, q["text"])
        if not r["clarifying_question"]:
            continue
        asked = 0
        while r["clarifying_question"] and asked < 2:
            asked += 1
            r = pipeline.answer(r["session_id"], r["clarifying_question"]["id"], _simulated_answer(r["clarifying_question"], q))
        got = "out_of_scope" if (r["out_of_scope"] or r["child_or_infant"]) else r["situation"]["id"]
        sub_ok = not q.get("subtype") or q["situation"] not in ("bites", "burns") or predicted_subtype(r) == q["subtype"]
        d = out.setdefault(q["lang"], {"ambiguous": 0, "resolved": 0})
        d["ambiguous"] += 1
        d["resolved"] += int(got == q["situation"] and sub_ok and not r["clarifying_question"])
    return out


def baselines(train: list[dict], test: list[dict]) -> dict[str, dict]:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
    except ImportError:
        print("scikit-learn not installed; skipping baselines (pip install -r requirements-offline.txt)")
        return {}
    res: dict[str, dict] = {}
    for target in ("situation", "urgency"):
        tr = [q for q in train if q.get(target)]
        model = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1), LogisticRegression(max_iter=2000))
        model.fit([q["text"] for q in tr], [q[target] for q in tr])
        for lang in LANGS:
            te = [q for q in test if q["lang"] == lang and q.get(target)]
            if not te:
                continue
            pred = model.predict([q["text"] for q in te])
            gold = [q[target] for q in te]
            r = res.setdefault(lang, {})
            if target == "situation":
                r["situation_accuracy"] = sum(g == p for g, p in zip(gold, pred)) / len(gold)
                r["situation_macro_f1"] = macro_f1(gold, list(pred), CLASSES)
            else:
                em = [p for g, p in zip(gold, pred) if g == "emergency"]
                r["missed_emergency_rate"] = sum(p != "emergency" for p in em) / len(em) if em else 0.0
                r["urgency_macro_f1"] = macro_f1(gold, list(pred), ["emergency", "clinic", "home"])
    return res


ORDER = ["missed_emergency_rate", "emergency_recall", "emergency_precision", "urgency_macro_f1", "situation_accuracy",
         "situation_macro_f1", "subtype_accuracy", "out_of_scope_f1", "slot_f1"]


def render(results: dict, base: dict, source: str) -> str:
    langs = [l for l in LANGS if l in results]
    lines = [
        "# Evaluation report",
        "",
        f"Data: `{source}` · model mode: `{config.MODEL_MODE}` · queries: {sum(results[l]['n'] for l in langs)}",
        "",
        "Safety measures come first. Gap = language minus English.",
        "",
        "| Metric | " + " | ".join(f"{l} (n={results[l]['n']})" for l in langs) + " |",
        "|---|" + "---|" * len(langs),
    ]
    en = results.get("en", {})
    for k in ORDER:
        cells = []
        for l in langs:
            v = results[l].get(k, 0.0)
            gap = "" if l == "en" or not en else f" ({v - en.get(k, 0.0):+.3f})"
            cells.append(f"{v:.3f}{gap}")
        lines.append(f"| {k} | " + " | ".join(cells) + " |")
    if base:
        lines += ["", "## Baseline: TF-IDF (char 2-4) + logistic regression", "", "| Metric | " + " | ".join(langs) + " |", "|---|" + "---|" * len(langs)]
        for k in ("missed_emergency_rate", "urgency_macro_f1", "situation_accuracy", "situation_macro_f1"):
            lines.append(f"| {k} | " + " | ".join(f"{base.get(l, {}).get(k, 0.0):.3f}" for l in langs) + " |")
    lines += ["", "Template-generated data measures the pipeline wiring, not real-world accuracy. Report research results on the hand-written test set (Section 10)."]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", type=Path, default=None)
    ap.add_argument("--baselines", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    qdir = ROOT / "data" / "queries"
    path = args.file
    if path is None:
        path = qdir / "test.jsonl"
        if not path.exists() or not load(path):
            path = qdir / "dev.jsonl"
    rows = load(path)
    results = evaluate(rows)
    base = baselines(load(qdir / "train.jsonl"), rows) if args.baselines else {}
    report = render(results, base, str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path))
    f2 = clarify_resolution(rows)
    if f2:
        report += "\n## F2: ambiguous queries resolved within 2 questions\n\n| Language | Ambiguous | Resolved | Share |\n|---|---|---|---|\n"
        for l in LANGS:
            if l in f2:
                d = f2[l]
                report += f"| {l} | {d['ambiguous']} | {d['resolved']} | {d['resolved'] / d['ambiguous']:.3f} |\n"
    print(report)
    if args.out:
        args.out.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
