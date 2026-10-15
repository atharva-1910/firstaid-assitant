# Evaluation report

Data: `data/queries/dev.jsonl` · model mode: `stub` · queries: 720

Safety measures come first. Gap = language minus English.

| Metric | en (n=180) | hi (n=180) | hinglish (n=180) | mr (n=180) |
|---|---|---|---|---|
| missed_emergency_rate | 0.000 | 0.000 (+0.000) | 0.000 (+0.000) | 0.000 (+0.000) |
| emergency_recall | 1.000 | 1.000 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| emergency_precision | 1.000 | 1.000 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| urgency_macro_f1 | 1.000 | 1.000 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| situation_accuracy | 1.000 | 1.000 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| situation_macro_f1 | 1.000 | 1.000 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| subtype_accuracy | 1.000 | 1.000 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| out_of_scope_f1 | 1.000 | 1.000 (+0.000) | 1.000 (+0.000) | 1.000 (+0.000) |
| slot_f1 | 0.990 | 0.966 (-0.024) | 0.965 (-0.025) | 0.944 (-0.046) |

## Baseline: TF-IDF (char 2-4) + logistic regression

| Metric | en | hi | hinglish | mr |
|---|---|---|---|---|
| missed_emergency_rate | 0.000 | 0.000 | 0.000 | 0.000 |
| urgency_macro_f1 | 1.000 | 1.000 | 1.000 | 1.000 |
| situation_accuracy | 1.000 | 1.000 | 1.000 | 1.000 |
| situation_macro_f1 | 1.000 | 1.000 | 1.000 | 1.000 |

Template-generated data measures the pipeline wiring, not real-world accuracy. Report research results on the hand-written test set (Section 10).

## F2: ambiguous queries resolved within 2 questions

| Language | Ambiguous | Resolved | Share |
|---|---|---|---|
| en | 32 | 32 | 1.000 |
| hi | 30 | 30 | 1.000 |
| hinglish | 33 | 33 | 1.000 |
| mr | 22 | 22 | 1.000 |
