# E7. Adversarial test for the step verifier

1309 pairs built from every step and do-not rule in four languages (`data/verifier/adversarial.jsonl`).
Cells: share handled correctly (dangerous rejected, safe accepted). Non-neural baselines; the trained mmBERT verifier is scored in `training/05_research_transformers.ipynb`.

| Candidate | Should be | Pairs | exact match | word overlap ≥ 0.75 | chrF ≥ 0.93 | chrF + number/negation guard |
|---|---|---|---|---|---|---|
| identity | accepted | 352 | 1.00 | 1.00 | 1.00 | 1.00 |
| polite_form | accepted | 100 | 0.00 | 0.95 | 0.68 | 0.68 |
| punctuation | accepted | 352 | 0.51 | 0.91 | 0.97 | 0.97 |
| antonym | rejected | 69 | 1.00 | 0.07 | 0.61 | 0.61 |
| call_dropped | rejected | 20 | 1.00 | 0.85 | 1.00 | 1.00 |
| negation_added | rejected | 174 | 1.00 | 0.14 | 0.13 | 1.00 |
| negation_removed | rejected | 178 | 1.00 | 0.11 | 0.45 | 1.00 |
| number_changed | rejected | 64 | 1.00 | 0.06 | 0.12 | 1.00 |

**By language** (dangerous rejected / safe accepted)

| Verifier | English | Hindi | Hinglish | Marathi |
|---|---|---|---|---|
| exact match | 1.00 / 0.94 | 1.00 / 0.44 | 1.00 / 0.85 | 1.00 / 0.44 |
| word overlap ≥ 0.75 | 0.14 / 0.99 | 0.13 / 0.85 | 0.12 / 1.00 | 0.17 / 0.99 |
| chrF ≥ 0.93 | 0.44 / 0.98 | 0.26 / 0.92 | 0.30 / 0.92 | 0.35 / 0.97 |
| chrF + number/negation guard | 0.97 / 0.98 | 0.94 / 0.92 | 0.94 / 0.92 | 0.94 / 0.97 |
