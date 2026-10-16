"""Extra per-student numbers for the CCA1 report (docs/research/report_extra.json).

    python -m research.report_extra

  slot F1 per language (F1 extraction) on dev and on the safety suite
  F2: ambiguous dev queries resolved within two questions, and questions asked per message
  language identification: word-list rules vs trained char n-gram model, per set and language, with confusion matrices
  situation confusion matrix (rules and the TF-IDF model) on safety-suite and probe messages
  cross-language safety net: emergencies missed when the language is forced wrong, without and with the net
"""
from __future__ import annotations

import os
from collections import Counter, defaultdict

from .common import LANGS, SITUATIONS, dev_rows, fit, probe_rows, rules_predict, safety_rows, train_rows, write_json


def slot_f1():
    from scripts.evaluate import evaluate

    out = {}
    for name, rows in (("dev (template)", dev_rows()),):
        res = evaluate(rows)
        out[name] = {l: res[l]["slot_f1"] for l in LANGS if l in res}
    return out


def clarify():
    from scripts.evaluate import clarify_resolution
    from app import pipeline
    from app.memory import store

    res = clarify_resolution(dev_rows())
    asked = defaultdict(Counter)
    for r in safety_rows() + probe_rows():
        store.clear()
        a = pipeline.analyze(None, r["text"])
        asked[r["lang"]]["question" if a["clarifying_question"] else "no question"] += 1
    return {"resolution": res, "hand_written_asked": {l: dict(c) for l, c in asked.items()}}


def langid():
    from app.models import NgramLanguageId
    from app.models.stub import StubLanguageId

    sets = {"dev (template)": dev_rows(), "safety suite": safety_rows(), "probe": probe_rows()}
    models = {"word-list rules": StubLanguageId(), "char n-gram model": NgramLanguageId()}
    out, conf = {}, {}
    for sname, rows in sets.items():
        out[sname] = {}
        for mname, m in models.items():
            pred = [m.detect(r["text"])["lang"] for r in rows]
            out[sname][mname] = {l: sum(p == r["lang"] for p, r in zip(pred, rows) if r["lang"] == l) / max(1, sum(r["lang"] == l for r in rows)) for l in LANGS}
            if sname == "probe":
                conf[mname] = [[sum(1 for p, r in zip(pred, rows) if r["lang"] == g and p == q) for q in LANGS] for g in LANGS]
    return {"accuracy": out, "probe_confusion": conf}


def confusion():
    rows = [r for r in safety_rows() + probe_rows() if r.get("situation")]
    m = fit("word+char", train_rows(), "situation")
    model = list(m.predict([r["text"] for r in rows]))
    rules = [rules_predict(r["text"])["situation"] for r in rows]
    mat = lambda pred: [[sum(1 for p, r in zip(pred, rows) if r["situation"] == g and p == q) for q in SITUATIONS] for g in SITUATIONS]  # noqa: E731
    return {"labels": SITUATIONS, "rules": mat(rules), "model": mat(model), "n": len(rows)}


def safety_net():
    """Safety-suite emergencies read with the wrong language (the sibling of the same script)."""
    from app import safety_rules
    from app.extract import SIBLING, extract, extract_safe

    out = {}
    for r in safety_rows():
        if not r["emergency"]:
            continue
        wrong = SIBLING[r["lang"]]
        d = out.setdefault(r["lang"], {"n": 0, "missed_plain": 0, "missed_net": 0, "forced_as": wrong})
        d["n"] += 1
        for key, f in (("missed_plain", extract), ("missed_net", extract_safe)):
            ex = f(r["text"], wrong)
            res = safety_rules.evaluate(ex.slots, ex.flags, ex.sits, ex.uncertain)
            if res.urgency != "emergency" and not res.child:
                d[key] += 1
    return out


def main():
    os.environ.setdefault("MODEL_MODE", "stub")
    out = {"slot_f1": slot_f1(), "clarify": clarify(), "langid": langid(), "confusion": confusion(), "safety_net": safety_net()}
    write_json("report_extra.json", out)
    for k, v in out.items():
        print(k, str(v)[:400])


if __name__ == "__main__":
    main()
