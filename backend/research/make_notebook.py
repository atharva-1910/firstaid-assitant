"""Writes training/05_research_transformers.ipynb (run on Colab with a GPU).

    python -m research.make_notebook
"""
from __future__ import annotations

import json

from .common import REPO

CELLS = [
    ("markdown", """# 05 · Research runs with transformers (whole team)

Runs the transformer half of the research experiments with the **same data, splits, noise and metrics** as the
CPU scripts in `backend/research/` (see `docs/research/README.md`), so the numbers go straight into the same tables.

| Part | Owner | What it adds | Time on a T4 |
|---|---|---|---|
| A. Multilingual sentence embeddings + logistic regression (LaBSE, BGE-M3, multilingual-E5) | Taneesha | E1 rows; the hybrid with the rules | ~10 min |
| B. Cross-lingual transfer with embeddings | Taneesha | E2 curve where 0% is real zero-shot | ~5 min |
| C. Fine-tuned MuRIL and IndicBERT v2 (situation and urgency) + robustness to noise | Soham, Atharva | E1 and E3 rows | ~30 min |
| D. mmBERT verifier on the adversarial set | Siddhi | E7 row (needs notebook 03 first) | ~5 min |
| E. Integrated Gradients for the urgency model + faithfulness test + sheet for human ratings | Soham | E8 rows, F4 plausibility | ~10 min |

Runtime → Change runtime type → **T4 GPU**. Run top to bottom. Results land in `docs/research/transformers_results.json`;
download it (last cell) and commit it, then run `python -m research.report` locally to refresh the tables.
Model ids were current in October 2026; check them on the Hugging Face Hub if a download fails."""),
    ("code", """!git clone -q https://github.com/atharva-1910/firstaid-assitant.git 2>/dev/null || true
%cd /content/firstaid-assitant/backend
!pip -q install -r requirements.txt
!pip -q install "transformers>=4.44" datasets accelerate sentence-transformers captum scikit-learn matplotlib"""),
    ("code", """import json, os, random, sys, time
import numpy as np, torch
os.environ["MODEL_MODE"] = "stub"
sys.path.insert(0, ".")
from research.common import *            # data, rules, metrics: the same code the CPU experiments use
from research.e1_models import score
from research.noise import NOISES
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", DEVICE)
seed_all()
train = train_rows()
SETS = eval_sets()                       # test (hand-written) first when it exists, then dev, safety suite, probe
RESULTS = {"created": time.strftime("%Y-%m-%d %H:%M"), "device": DEVICE}
for k, v in SETS.items(): print(k, len(v))"""),
    ("markdown", "## A. Multilingual sentence embeddings + logistic regression"),
    ("code", """from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression

EMBEDDERS = {
    "LaBSE": ("sentence-transformers/LaBSE", ""),
    "BGE-M3": ("BAAI/bge-m3", ""),
    "multilingual-E5-base": ("intfloat/multilingual-e5-base", "query: "),
}
ALL_ROWS = train + [r for rows in SETS.values() for r in rows]
TEXTS = sorted({r["text"] for r in ALL_ROWS})
EMB = {}
for label, (name, prefix) in EMBEDDERS.items():
    m = SentenceTransformer(name, device=DEVICE)
    vecs = m.encode([prefix + t for t in TEXTS], batch_size=64, normalize_embeddings=True, show_progress_bar=True)
    EMB[label] = dict(zip(TEXTS, vecs))
    del m; torch.cuda.empty_cache()

def X(label, rows): return np.stack([EMB[label][r["text"]] for r in rows])

def fit_lr(label, rows, target):
    rs = [r for r in rows if r.get(target)]
    return LogisticRegression(C=10.0, max_iter=3000).fit(X(label, rs), [r[target] for r in rs])"""),
    ("code", """RESULTS["A_embeddings"] = {}
rules_cache = {}
for set_name, rows in SETS.items():
    rules_cache[set_name] = [rules_predict(r["text"]) for r in rows]
for label in EMBEDDERS:
    sit_m, urg_m = fit_lr(label, train, "situation"), fit_lr(label, train, "urgency")
    em_i = list(urg_m.classes_).index("emergency")
    RESULTS["A_embeddings"][label] = {}
    for set_name, rows in SETS.items():
        Xs = X(label, rows)
        sit, pem = sit_m.predict(Xs), urg_m.predict_proba(Xs)[:, em_i]
        model_preds = [{"situation": s, "emergency": bool(p >= 0.5)} for s, p in zip(sit, pem)]
        hybrid = [{"situation": r["situation"], "emergency": r["emergency"] or m["emergency"]} for r, m in zip(rules_cache[set_name], model_preds)]
        idx = by_lang(rows)
        RESULTS["A_embeddings"][label][set_name] = {
            "model": {l: score(rows, model_preds, idx[l]) for l in LANGS if idx.get(l)} | {"all": score(rows, model_preds, list(range(len(rows))))},
            "hybrid": {l: score(rows, hybrid, idx[l]) for l in LANGS if idx.get(l)} | {"all": score(rows, hybrid, list(range(len(rows))))},
        }
        a = RESULTS["A_embeddings"][label][set_name]
        print(f"{label:22s} {set_name:38s} sit={a['model']['all']['situation_acc'][0]:.2f} em_recall={a['model']['all']['emergency_recall'][0]:.2f} "
              f"FA={a['model']['all']['false_alarm_rate'][0]:.2f} | hybrid em_recall={a['hybrid']['all']['emergency_recall'][0]:.2f}")"""),
    ("markdown", "## B. Cross-lingual transfer with embeddings (0% = zero-shot from English)"),
    ("code", """FRACTIONS = [0.0, 0.05, 0.10, 0.25, 0.50, 1.0]
RESULTS["B_transfer"] = {}
test_sets = {"dev (template)": dev_rows(), "probe": probe_rows()}
en = [r for r in train if r["lang"] == "en"]
for label in EMBEDDERS:
    RESULTS["B_transfer"][label] = {}
    for tgt in ["hi", "hinglish", "mr"]:
        pool = [r for r in train if r["lang"] == tgt]
        RESULTS["B_transfer"][label][tgt] = {}
        for frac in FRACTIONS:
            accs = {k: [] for k in test_sets}
            for seed in ([SEED, SEED + 1, SEED + 2] if 0 < frac < 1 else [SEED]):
                rows = en + random.Random(seed).sample(pool, int(round(frac * len(pool))))
                m = fit_lr(label, rows, "situation")
                for k, ts in test_sets.items():
                    t = [r for r in ts if r["lang"] == tgt and r.get("situation")]
                    accs[k].append(float(np.mean(m.predict(X(label, t)) == np.array([r["situation"] for r in t]))))
            RESULTS["B_transfer"][label][tgt][str(frac)] = {k: [float(np.mean(v)), float(np.std(v))] for k, v in accs.items()}
        print(label, tgt, [round(RESULTS["B_transfer"][label][tgt][str(f)]["probe"][0], 2) for f in FRACTIONS])"""),
    ("markdown", "## C. Fine-tuned MuRIL and IndicBERT v2"),
    ("code", """from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, DataCollatorWithPadding

ENCODERS = {"MuRIL": "google/muril-base-cased", "IndicBERT v2": "ai4bharat/IndicBERTv2-MLM-only"}

def make_trainer(model, args, tok, train_ds=None):
    kw = dict(model=model, args=args, train_dataset=train_ds, data_collator=DataCollatorWithPadding(tok))
    try:
        return Trainer(processing_class=tok, **kw)
    except TypeError:                      # older transformers
        return Trainer(tokenizer=tok, **kw)

def finetune(name, rows, target, epochs=3, seed=SEED):
    rs = [r for r in rows if r.get(target)]
    labels = sorted({r[target] for r in rs})
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForSequenceClassification.from_pretrained(name, num_labels=len(labels),
              id2label=dict(enumerate(labels)), label2id={l: i for i, l in enumerate(labels)})
    ds = Dataset.from_dict({"text": [r["text"] for r in rs], "label": [labels.index(r[target]) for r in rs]})
    ds = ds.map(lambda b: tok(b["text"], truncation=True, max_length=96), batched=True).remove_columns(["text"])
    args = TrainingArguments(f"/content/out_{target}", per_device_train_batch_size=32, learning_rate=3e-5, num_train_epochs=epochs,
                             fp16=torch.cuda.is_available(), save_strategy="no", report_to=[], seed=seed, logging_steps=50)
    make_trainer(model, args, tok, ds).train()
    model.eval()
    return tok, model, labels

@torch.no_grad()
def predict_proba(tok, model, texts, bs=64):
    out = []
    for i in range(0, len(texts), bs):
        enc = tok(texts[i:i + bs], truncation=True, max_length=96, padding=True, return_tensors="pt").to(model.device)
        out.append(torch.softmax(model(**enc).logits, -1).cpu().numpy())
    return np.concatenate(out)

FT = {}
for label, name in ENCODERS.items():
    FT[label] = {"situation": finetune(name, train, "situation"), "urgency": finetune(name, train, "urgency")}
    print("trained", label)"""),
    ("code", """def ft_preds(label, texts):
    tok_s, m_s, lab_s = FT[label]["situation"]
    tok_u, m_u, lab_u = FT[label]["urgency"]
    ps, pu = predict_proba(tok_s, m_s, texts), predict_proba(tok_u, m_u, texts)
    em_i = lab_u.index("emergency")
    return [{"situation": lab_s[a], "emergency": bool(b[em_i] >= 0.5), "p_em": float(b[em_i])} for a, b in zip(ps.argmax(1), pu)]

RESULTS["C_finetuned"] = {}
for label in ENCODERS:
    RESULTS["C_finetuned"][label] = {}
    for set_name, rows in SETS.items():
        mp = ft_preds(label, [r["text"] for r in rows])
        hybrid = [{"situation": r["situation"], "emergency": r["emergency"] or m["emergency"]} for r, m in zip(rules_cache[set_name], mp)]
        idx = by_lang(rows)
        RESULTS["C_finetuned"][label][set_name] = {
            "model": {l: score(rows, mp, idx[l]) for l in LANGS if idx.get(l)} | {"all": score(rows, mp, list(range(len(rows))))},
            "hybrid": {l: score(rows, hybrid, idx[l]) for l in LANGS if idx.get(l)} | {"all": score(rows, hybrid, list(range(len(rows))))},
        }
        a = RESULTS["C_finetuned"][label][set_name]
        print(f"{label:13s} {set_name:38s} sit={a['model']['all']['situation_acc'][0]:.2f} em_recall={a['model']['all']['emergency_recall'][0]:.2f} "
              f"FA={a['model']['all']['false_alarm_rate'][0]:.2f} | hybrid em_recall={a['hybrid']['all']['emergency_recall'][0]:.2f}")"""),
    ("code", """# Robustness (E3) for the fine-tuned models: same noise, same safety-suite and probe messages, same seeds.
LEVELS = [0.0, 0.1, 0.2, 0.3, 0.5]
hw = safety_rows() + probe_rows()
RESULTS["C_robustness"] = {}
for label in ENCODERS:
    RESULTS["C_robustness"][label] = {}
    for noise, f in NOISES.items():
        RESULTS["C_robustness"][label][noise] = {}
        for level in LEVELS:
            runs = []
            for seed in ([SEED, SEED + 1, SEED + 2] if level else [SEED]):
                rng = random.Random(seed)
                texts = [f(r["text"], r["lang"], level, rng) if level else r["text"] for r in hw]
                p = ft_preds(label, texts)
                sit = [r["situation"] == q["situation"] for r, q in zip(hw, p) if r.get("situation")]
                rec = [q["emergency"] for r, q in zip(hw, p) if is_emergency(r)]
                fa = [q["emergency"] for r, q in zip(hw, p) if is_emergency(r) is False]
                runs.append((np.mean(sit), np.mean(rec), np.mean(fa)))
            RESULTS["C_robustness"][label][noise][str(level)] = dict(zip(["situation_acc", "emergency_recall", "false_alarm"], np.mean(runs, 0).tolist()))
        print(label, noise, {l: round(RESULTS["C_robustness"][label][noise][str(l)]["emergency_recall"], 2) for l in LEVELS})"""),
    ("markdown", "## D. mmBERT verifier on the adversarial set (run notebook 03 first)"),
    ("code", """VER = "../training/out/mmbert_verifier"   # written by notebook 03 (label 0 = entailment)
pairs = jsonl(BACKEND / "data" / "verifier" / "adversarial.jsonl")
if os.path.isdir(VER):
    vtok = AutoTokenizer.from_pretrained(VER)
    vmod = AutoModelForSequenceClassification.from_pretrained(VER).to(DEVICE).eval()
    @torch.no_grad()
    def entails(a, b, bs=64):
        out = []
        for i in range(0, len(a), bs):
            enc = vtok(a[i:i + bs], b[i:i + bs], truncation=True, max_length=192, padding=True, return_tensors="pt").to(DEVICE)
            out += (vmod(**enc).logits.argmax(-1) == 0).tolist()
        return np.array(out)
    P, H = [p["premise"] for p in pairs], [p["hypothesis"] for p in pairs]
    accepted = entails(P, H) & entails(H, P)          # the app accepts only when it holds both ways
    by = {}
    for p, acc in zip(pairs, accepted):
        ok = acc if p["label"] == "same" else not acc
        for k in (p["kind"], f"{p['lang']}:{p['label']}", p["label"]):
            by.setdefault(k, []).append(bool(ok))
    RESULTS["D_verifier"] = {k: float(np.mean(v)) for k, v in by.items()}
    for k, v in sorted(RESULTS["D_verifier"].items()): print(f"{k:28s} {v:.2f}")
else:
    print("No verifier found at", VER, "- run training/03_verifier_mmbert.ipynb first.")"""),
    ("markdown", "## E. Integrated Gradients for the urgency model, faithfulness, and a sheet for human ratings"),
    ("code", """from captum.attr import LayerIntegratedGradients
label = "IndicBERT v2"
tok_u, m_u, lab_u = FT[label]["urgency"]
EM = lab_u.index("emergency")

def forward(ids, mask): return torch.softmax(m_u(input_ids=ids, attention_mask=mask).logits, -1)[:, EM]
lig = LayerIntegratedGradients(forward, m_u.get_input_embeddings())

def word_attr(text):
    words = text.split()
    enc = tok_u(words, is_split_into_words=True, truncation=True, max_length=96, return_tensors="pt").to(m_u.device)
    ids, mask = enc["input_ids"], enc["attention_mask"]
    base = torch.full_like(ids, tok_u.pad_token_id)
    special = torch.tensor([[t in tok_u.all_special_ids for t in ids[0].tolist()]], device=ids.device)
    base[special] = ids[special]
    att = lig.attribute(ids, baselines=base, additional_forward_args=(mask,), n_steps=32).sum(-1)[0].detach().cpu().numpy()
    per_word = np.zeros(len(words))
    for ti, wi in enumerate(enc.word_ids()):
        if wi is not None: per_word[wi] += att[ti]
    return words, per_word

def p_em(texts): return predict_proba(tok_u, m_u, texts)[:, EM]
def drop(words, idx):
    kept = [w for i, w in enumerate(words) if i not in idx]
    return " ".join(kept) if kept else "."

rows = [r for r in hw if is_emergency(r)]
base = p_em([r["text"] for r in rows]); keep = [i for i, p in enumerate(base) if p >= 0.5]
rng = random.Random(SEED); res = {"messages": len(keep)}; sheet = []
for k in (1, 2, 3):
    top, rnd = [], []
    for i in keep:
        words, a = word_attr(rows[i]["text"]); kk = min(k, max(1, len(words) - 1))
        order = list(np.argsort(-a))
        top.append(drop(words, set(order[:kk]))); rnd.append(drop(words, set(rng.sample(range(len(words)), kk))))
        if k == 3: sheet.append({"id": rows[i]["id"], "lang": rows[i]["lang"], "text": rows[i]["text"],
                                 "top_words": " | ".join(words[j] for j in order[:3]), "rater1_relevant (y/n)": "", "rater2_relevant (y/n)": ""})
    pt, pr = p_em(top), p_em(rnd)
    res[f"top{k}"] = {"comprehensiveness": float(np.mean(base[keep] - pt)), "flip_rate": float(np.mean(pt < 0.5))}
    res[f"random{k}"] = {"comprehensiveness": float(np.mean(base[keep] - pr)), "flip_rate": float(np.mean(pr < 0.5))}
RESULTS["E_integrated_gradients"] = res
print(json.dumps(res, indent=1))
import csv
with open("../docs/research/f4_plausibility_sheet.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(sheet[0])); w.writeheader(); w.writerows(sheet)
print("Two people mark each row: are the highlighted words why this is an emergency? Then run research/agreement.py on the sheet.")"""),
    ("code", """OUT.mkdir(parents=True, exist_ok=True)
(OUT / "transformers_results.json").write_text(json.dumps(RESULTS, indent=1, ensure_ascii=False, default=float), encoding="utf-8")
from google.colab import files
files.download(str(OUT / "transformers_results.json"))
files.download("../docs/research/f4_plausibility_sheet.csv")"""),
]


def main():
    nb = {
        "cells": [
            {"cell_type": t, "metadata": {}, "source": src.splitlines(keepends=True), **({"outputs": [], "execution_count": None} if t == "code" else {})}
            for t, src in CELLS
        ],
        "metadata": {"accelerator": "GPU", "colab": {"provenance": []}, "kernelspec": {"display_name": "Python 3", "name": "python3"},
                     "language_info": {"name": "python"}},
        "nbformat": 4,
        "nbformat_minor": 0,
    }
    p = REPO / "training" / "05_research_transformers.ipynb"
    p.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", p)


if __name__ == "__main__":
    main()
