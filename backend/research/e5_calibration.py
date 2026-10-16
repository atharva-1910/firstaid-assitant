"""E5. Calibration and selective prediction (the "ask a question when unsure" decision).

    python -m research.e5_calibration

For the situation classifier (TF-IDF words + chars + LR) and for the app's own rule-based
confidence: reliability diagram, expected calibration error (ECE, 10 equal-width bins) and the
risk-coverage curve (sort by confidence; answer only the most confident share, ask a question
for the rest). Also reports what the app's fixed thresholds (ask if confidence < 0.75) do:
how many messages get a question, and the accuracy on the ones that do not.
"""
from __future__ import annotations

import os

import numpy as np

from .common import SITUATIONS, dev_rows, fit, md_table, probe_rows, safety_rows, train_rows, write_json
from .plotting import SERIES, plt, save

APP_THRESHOLD = 0.75


def ece(conf: np.ndarray, correct: np.ndarray, bins: int = 10) -> tuple[float, list]:
    edges = np.linspace(0, 1, bins + 1)
    total, table = 0.0, []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi) if lo > 0 else (conf >= lo) & (conf <= hi)
        if m.any():
            gap = abs(conf[m].mean() - correct[m].mean())
            total += m.mean() * gap
            table.append((float(lo), float(hi), int(m.sum()), float(conf[m].mean()), float(correct[m].mean())))
    return float(total), table


def risk_coverage(conf: np.ndarray, correct: np.ndarray) -> tuple[list[float], list[float], float]:
    order = np.argsort(-conf, kind="stable")
    c = correct[order]
    cov = np.arange(1, len(c) + 1) / len(c)
    risk = 1 - np.cumsum(c) / np.arange(1, len(c) + 1)
    return cov.tolist(), risk.tolist(), float(np.mean(risk))  # last value = AURC (area under the curve)


def rules_confidence(rows):
    os.environ.setdefault("MODEL_MODE", "stub")
    from app import pipeline
    from app.memory import store

    conf, pred, asked = [], [], []
    for r in rows:
        store.clear()
        out = pipeline.analyze(None, r["text"])
        s = out["situation"]["id"]
        s = "out_of_scope" if out.get("child_or_infant") or out.get("out_of_scope") or s not in SITUATIONS else s
        conf.append(float(out["situation"]["confidence"]))
        pred.append(s)
        asked.append(out["next_screen"] == "question" or out["clarifying_question"] is not None)
    return np.array(conf), pred, np.array(asked)


def main():
    model = fit("word+char", train_rows(), "situation")
    sets = {"dev (template)": dev_rows(), "safety suite + probe": safety_rows() + probe_rows()}
    results, curves = {}, {}
    for name, rows in sets.items():
        rows = [r for r in rows if r.get("situation")]
        gold = np.array([r["situation"] for r in rows])
        proba = model.predict_proba([r["text"] for r in rows])
        m_conf = proba.max(axis=1)
        m_correct = (model.classes_[proba.argmax(axis=1)] == gold).astype(float)
        r_conf, r_pred, asked = rules_confidence(rows)
        r_correct = (np.array(r_pred) == gold).astype(float)
        res = {}
        for sys, conf, correct in (("model", m_conf, m_correct), ("rules (app confidence)", r_conf, r_correct)):
            e, table = ece(conf, correct)
            cov, risk, aurc = risk_coverage(conf, correct)
            keep = conf >= APP_THRESHOLD
            res[sys] = {
                "accuracy": float(correct.mean()), "ece": e, "aurc": aurc, "bins": table,
                "threshold_0.75": {"answered_share": float(keep.mean()), "accuracy_answered": float(correct[keep].mean()) if keep.any() else float("nan"),
                                   "accuracy_questioned": float(correct[~keep].mean()) if (~keep).any() else float("nan")},
            }
            curves[(name, sys)] = (cov, risk, table)
        res["rules (app confidence)"]["app_asked_question_share"] = float(asked.mean())
        res["rules (app confidence)"]["accuracy_when_app_did_not_ask"] = float(r_correct[~asked].mean()) if (~asked).any() else float("nan")
        results[name] = res
        print(name, {k: (round(v["accuracy"], 3), round(v["ece"], 3), round(v["aurc"], 3), v["threshold_0.75"]) for k, v in res.items()})
    write_json("e5_calibration.json", results)

    md = ["# E5. Calibration and selective prediction", "",
          "ECE = expected calibration error (lower is better). AURC = area under the risk-coverage curve (lower is better).",
          "At 0.75: share of messages answered without a question at the app's threshold, and accuracy on those vs on the rest.", ""]
    rows = []
    for name, res in results.items():
        for sys, d in res.items():
            t = d["threshold_0.75"]
            rows.append([name, sys, f"{d['accuracy']:.2f}", f"{d['ece']:.3f}", f"{d['aurc']:.3f}", f"{100 * t['answered_share']:.0f}%",
                         f"{t['accuracy_answered']:.2f}", f"{t['accuracy_questioned']:.2f}" if t["accuracy_questioned"] == t["accuracy_questioned"] else "–"])
    md.append(md_table(["Set", "Confidence from", "Accuracy", "ECE", "AURC", "Answered at 0.75", "Acc. answered", "Acc. would-ask"], rows))
    for name, res in results.items():
        r = res["rules (app confidence)"]
        md += ["", f"In the app ({name}): a question was asked for {100 * r['app_asked_question_share']:.0f}% of messages; accuracy on the rest was {r['accuracy_when_app_did_not_ask']:.2f}."]
    (write_json.__globals__["OUT"] / "e5_calibration.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.4))
    hw = "safety suite + probe"
    axes[0].plot([0, 1], [0, 1], color="#c3c2b7", linewidth=1, linestyle="--", label="perfect calibration")
    for i, sys in enumerate(("model", "rules (app confidence)")):
        cov, risk, table = curves[(hw, sys)]
        axes[0].plot([t[3] for t in table], [t[4] for t in table], marker="o", color=SERIES[i], label=sys)
        axes[1].plot(cov, risk, color=SERIES[i], label=sys)
    axes[0].set_xlabel("Mean confidence in bin")
    axes[0].set_ylabel("Accuracy in bin")
    axes[0].set_title("Reliability (safety suite + probe)")
    axes[0].set_xlim(0, 1.02)
    axes[0].set_ylim(0, 1.02)
    axes[0].legend(fontsize=8, loc="upper left")
    axes[1].set_xlabel("Coverage (share answered without a question)")
    axes[1].set_ylabel("Error rate on answered")
    axes[1].set_title("Risk–coverage (safety suite + probe)")
    axes[1].set_ylim(0, None)
    save(fig, "e5_calibration.png")


if __name__ == "__main__":
    main()
