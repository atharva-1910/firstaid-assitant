"""E8. Are the highlighted words really why the alert fired? (F4, owner Soham)

    python -m research.e8_faithfulness

For emergency messages (safety suite + probe) that a model flags as emergencies, each word gets
an attribution from the linear model itself (sum of tf-idf value x weight of the features in
that word, for the emergency class against the others): no deletion is involved, so the deletion
test below is a fair check. Then, ERASER-style (DeYoung et al., 2020):

  comprehensiveness  drop in P(emergency) when the top-k words are deleted (higher = more faithful)
  flip rate          share of alerts that disappear when the top-k words are deleted
  baseline           the same with k random words deleted

The app's own F4 explanation (the rule trigger words) is checked the same way: delete the
trigger words and see whether the rules still raise the alert, and whether the model agrees
they matter. Agreement = share of messages where the model's top word is one of the trigger words.
"""
from __future__ import annotations

import random
import re

import numpy as np

from .common import SEED, is_emergency, md_table, probe_rows, rules_predict, safety_rows, train_rows, write_json
from .plotting import grouped_bars, legend_below, plt, save

WORD = re.compile(r"\S+")
KS = [1, 2, 3]


def fit_unigram(rows, analyzer: str):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 1), sublinear_tf=True, token_pattern=r"(?u)\b\w+\b") if analyzer == "word" \
        else TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)
    m = Pipeline([("tfidf", vec), ("clf", LogisticRegression(C=10.0, max_iter=3000))])
    rs = [r for r in rows if r.get("urgency")]
    m.fit([r["text"] for r in rs], [r["urgency"] for r in rs])
    return m


def p_em(m, texts):
    i = list(m.classes_).index("emergency")
    return m.predict_proba(texts)[:, i]


def word_attributions(m, text: str) -> list[tuple[int, float]]:
    vec, clf = m.named_steps["tfidf"], m.named_steps["clf"]
    i = list(clf.classes_).index("emergency")
    w = clf.coef_[i] - np.delete(clf.coef_, i, axis=0).mean(axis=0)
    x = vec.transform([text])
    analyze = vec.build_analyzer()
    vocab = vec.vocabulary_
    out = []
    for wi, tok in enumerate(WORD.findall(text)):
        feats = analyze(tok)
        idx = {vocab[f] for f in feats if f in vocab}
        out.append((wi, float(sum(x[0, j] * w[j] for j in idx))))
    return sorted(out, key=lambda t: -t[1])


def delete(text: str, idx: set[int]) -> str:
    ws = WORD.findall(text)
    kept = [w for i, w in enumerate(ws) if i not in idx]
    return " ".join(kept) if kept else "."


def rule_trigger_idx(text: str) -> set[int]:
    import os

    os.environ.setdefault("MODEL_MODE", "stub")
    from app import pipeline
    from app.memory import store

    store.clear()
    r = pipeline.analyze(None, text)
    spans = [(e["start"], e["end"]) for e in r.get("explanation", [])]
    idx, pos = set(), 0
    for wi, m in enumerate(WORD.finditer(text)):
        if any(m.start() < e and m.end() > s for s, e in spans):
            idx.add(wi)
    return idx


def main():
    rng = random.Random(SEED)
    train = train_rows()
    rows = [r for r in safety_rows() + probe_rows() if is_emergency(r)]
    results = {}
    for name in ("word", "char"):
        m = fit_unigram(train, name)
        base = p_em(m, [r["text"] for r in rows])
        keep = [i for i, p in enumerate(base) if p >= 0.5]
        res = {"messages": len(keep)}
        for k in KS:
            top_t, rnd_t = [], []
            for i in keep:
                t = rows[i]["text"]
                att = word_attributions(m, t)
                n = len(att)
                kk = min(k, max(1, n - 1)) if n > 1 else 1
                top_t.append(delete(t, {wi for wi, _ in att[:kk]}))
                rnd_t.append(delete(t, set(rng.sample(range(n), kk)) if n > 1 else {0}))
            pt, pr = p_em(m, top_t), p_em(m, rnd_t)
            b = base[keep]
            res[f"top{k}"] = {"comprehensiveness": float(np.mean(b - pt)), "flip_rate": float(np.mean(pt < 0.5))}
            res[f"random{k}"] = {"comprehensiveness": float(np.mean(b - pr)), "flip_rate": float(np.mean(pr < 0.5))}
        # The app's F4 words: trigger words of the rules.
        trig_t, agree, rules_flip, n_trig = [], [], [], 0
        for i in keep:
            t = rows[i]["text"]
            idx = rule_trigger_idx(t)
            if not idx:
                continue
            n_trig += 1
            trig_t.append(delete(t, idx))
            agree.append(word_attributions(m, t)[0][0] in idx)
            rules_flip.append(not rules_predict(delete(t, idx))["emergency"])
        pt = p_em(m, trig_t) if trig_t else np.array([])
        sel = [i for i in keep if rule_trigger_idx(rows[i]["text"])]
        res["rule_trigger_words"] = {
            "messages_with_triggers": n_trig,
            "model_comprehensiveness": float(np.mean(base[sel] - pt)) if trig_t else float("nan"),
            "model_flip_rate": float(np.mean(pt < 0.5)) if trig_t else float("nan"),
            "rules_flip_rate": float(np.mean(rules_flip)) if rules_flip else float("nan"),
            "model_top_word_is_trigger": float(np.mean(agree)) if agree else float("nan"),
        }
        results[name] = res
        print(name, res)
    write_json("e8_faithfulness.json", results)

    labels = {"word": "word model", "char": "character model"}
    md = ["# E8. Faithfulness of explanations (F4)", "",
          "Emergency messages from the safety suite and probe that the model flags. Comprehensiveness = mean drop in P(emergency) after deleting the words; flip = alert disappears.", ""]
    rows_md = []
    for name, res in results.items():
        for k in KS:
            rows_md.append([labels[name], f"top {k} attributed", f"{res[f'top{k}']['comprehensiveness']:.2f}", f"{100 * res[f'top{k}']['flip_rate']:.0f}%"])
            rows_md.append([labels[name], f"{k} random", f"{res[f'random{k}']['comprehensiveness']:.2f}", f"{100 * res[f'random{k}']['flip_rate']:.0f}%"])
        t = res["rule_trigger_words"]
        rows_md.append([labels[name], "app's trigger words (F4)", f"{t['model_comprehensiveness']:.2f}", f"{100 * t['model_flip_rate']:.0f}%"])
    md.append(md_table(["Model", "Words deleted", "Comprehensiveness", "Alerts that disappear"], rows_md))
    t = results["word"]["rule_trigger_words"]
    md += ["", f"Rules: deleting the app's own trigger words removes the rule alert in {100 * t['rules_flip_rate']:.0f}% of {t['messages_with_triggers']} messages "
           "(the rest still fire on other words). The word model's top word is one of the app's trigger words in "
           f"{100 * t['model_top_word_is_trigger']:.0f}% of messages (character model: {100 * results['char']['rule_trigger_words']['model_top_word_is_trigger']:.0f}%)."]
    (write_json.__globals__["OUT"] / "e8_faithfulness.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(6.4, 3.9))
    grouped_bars(ax, [f"k = {k}" for k in KS], {
        "top-k attributed (word model)": [results["word"][f"top{k}"]["flip_rate"] for k in KS],
        "k random words (word model)": [results["word"][f"random{k}"]["flip_rate"] for k in KS],
        "top-k attributed (char model)": [results["char"][f"top{k}"]["flip_rate"] for k in KS],
    })
    ax.set_ylabel("Alerts that disappear")
    ax.set_title("Deleting the highlighted words removes the alert")
    legend_below(ax, 2)
    save(fig, "e8_faithfulness.png")


if __name__ == "__main__":
    main()
