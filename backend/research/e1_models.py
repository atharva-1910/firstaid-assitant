"""E1. Rules vs classical models vs the hybrid, for situation and emergency detection.

    python -m research.e1_models

Models train on train.jsonl (template data, all four languages) and are tested on every
evaluation set, per language, with 95% bootstrap intervals. The hybrid keeps the rules floor and
lets the model only *raise* urgency: emergency = rules say emergency OR model says emergency.
On the probe set the rules are also shown as they were before the probe-driven lexicon fixes
(commit 33802b7), because the current lexicons were corrected by looking at those very messages.
"""
from __future__ import annotations

from .common import (LANG_NAMES, LANGS, MODEL_LABELS, bootstrap_ci, by_lang, eval_sets, fit, fmt_ci, is_emergency,
                     macro_f1, md_table, rules_predict, rules_predict_at, seed_all, train_rows, write_json)
from .plotting import grouped_bars, legend_below, plt, save

BEFORE_PROBE_FIX = "33802b7"
HYBRID_THRESHOLD = 0.3  # the model may also raise urgency when P(emergency) >= this


def predict_all(rows: list[dict], models: dict, set_name: str) -> dict[str, list[dict]]:
    texts = [r["text"] for r in rows]
    preds: dict[str, list[dict]] = {}
    rules = [rules_predict(t) for t in texts]
    preds["rules"] = rules
    if set_name.startswith("probe"):
        preds[f"rules before probe fixes ({BEFORE_PROBE_FIX})"] = rules_predict_at(BEFORE_PROBE_FIX, texts)
    for kind, (sit_m, urg_m) in models.items():
        sit = sit_m.predict(texts)
        urg_p = urg_m.predict_proba(texts)
        em_i = list(urg_m.classes_).index("emergency")
        preds[MODEL_LABELS[kind]] = [
            {"situation": s, "emergency": bool(p.argmax() == em_i), "p_em": float(p[em_i])} for s, p in zip(sit, urg_p)
        ]
    # Hybrid: rules floor, best model may only raise urgency.
    best = preds[MODEL_LABELS["word+char"]]
    preds["hybrid: rules + model (argmax)"] = [
        {"situation": r["situation"], "emergency": r["emergency"] or m["emergency"]} for r, m in zip(rules, best)
    ]
    preds[f"hybrid: rules + model (P≥{HYBRID_THRESHOLD})"] = [
        {"situation": r["situation"], "emergency": r["emergency"] or m["p_em"] >= HYBRID_THRESHOLD} for r, m in zip(rules, best)
    ]
    old = preds.get(f"rules before probe fixes ({BEFORE_PROBE_FIX})")
    if old:
        # What the hybrid would have done before anyone fixed the lexicons by reading these messages.
        preds["hybrid: rules before fixes + model"] = [
            {"situation": r["situation"], "emergency": r["emergency"] or m["emergency"]} for r, m in zip(old, best)
        ]
    return preds


def score(rows: list[dict], preds: list[dict], idx: list[int]) -> dict:
    sit = [(rows[i]["situation"], preds[i]["situation"]) for i in idx if rows[i].get("situation")]
    em = [(is_emergency(rows[i]), preds[i]["emergency"]) for i in idx if is_emergency(rows[i]) is not None]
    hits_sit = [int(g == p) for g, p in sit]
    rec = [int(p) for g, p in em if g]
    fa = [int(p) for g, p in em if not g]
    return {
        "n_situation": len(sit),
        "situation_acc": bootstrap_ci(hits_sit),
        "situation_macro_f1": macro_f1([g for g, _ in sit], [p for _, p in sit]),
        "n_emergency": len(rec),
        "emergency_recall": bootstrap_ci(rec),
        "missed_emergencies": int(len(rec) - sum(rec)),
        "n_non_emergency": len(fa),
        "false_alarm_rate": bootstrap_ci(fa),
    }


def main():
    seed_all()
    train = train_rows()
    models = {k: (fit(k, train, "situation"), fit(k, train, "urgency")) for k in MODEL_LABELS}
    results: dict = {}
    md = ["# E1. Rules vs classical models vs hybrid", "",
          "Trained on `train.jsonl` (2,880 template messages). 95% bootstrap intervals in brackets.",
          "Probe labels are silver (labelled by Claude, to be checked by the team).", ""]
    for set_name, rows in eval_sets().items():
        preds = predict_all(rows, models, set_name)
        idx = by_lang(rows)
        results[set_name] = {sys: {l: score(rows, p, idx[l]) for l in LANGS if idx.get(l)} | {"all": score(rows, p, list(range(len(rows))))}
                             for sys, p in preds.items()}
        md += [f"## {set_name}", "", "**Situation accuracy**", ""]
        md.append(md_table(["System"] + [LANG_NAMES[l] for l in LANGS] + ["All"],
                           [[s] + [fmt_ci(results[set_name][s][l]["situation_acc"]) for l in LANGS + ["all"]] for s in preds]))
        md += ["", "**Emergency recall** (missed emergencies in brackets after the interval)", ""]
        md.append(md_table(["System"] + [LANG_NAMES[l] for l in LANGS] + ["All"],
                           [[s] + [f"{fmt_ci(results[set_name][s][l]['emergency_recall'])} ({results[set_name][s][l]['missed_emergencies']} missed)"
                                   for l in LANGS + ["all"]] for s in preds]))
        md += ["", "**False-alarm rate** (non-emergencies flagged as emergency)", ""]
        md.append(md_table(["System", "All"], [[s, fmt_ci(results[set_name][s]["all"]["false_alarm_rate"])] for s in preds]))
        md.append("")
    write_json("e1_models.json", results)
    (write_json.__globals__["OUT"] / "e1_models.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # Figure: emergency recall per language on the probe set
    probe = next(k for k in results if k.startswith("probe"))
    show = [f"rules before probe fixes ({BEFORE_PROBE_FIX})", MODEL_LABELS["word+char"], "hybrid: rules before fixes + model"]
    names = ["Rules (before probe fixes)", "Model (TF-IDF words+chars)", "Hybrid (same rules + model)"]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    vals = {n: [results[probe][s][l]["emergency_recall"][0] for l in LANGS] for n, s in zip(names, show)}
    errs = {n: [results[probe][s][l]["emergency_recall"][1:] for l in LANGS] for n, s in zip(names, show)}
    grouped_bars(ax, [LANG_NAMES[l] for l in LANGS], vals, errs)
    ax.set_ylabel("Emergency recall")
    ax.set_title("Probe set: emergencies caught, per language")
    legend_below(ax, 3)
    save(fig, "e1_probe_emergency_recall.png")
    print("\n".join(md[:3]))
    for s in preds:
        r = results[probe][s]["all"]
        print(f"{s:45s} probe sit {r['situation_acc'][0]:.2f}  em-recall {r['emergency_recall'][0]:.2f} missed {r['missed_emergencies']}  FA {r['false_alarm_rate'][0]:.2f}")


if __name__ == "__main__":
    main()
