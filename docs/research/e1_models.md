# E1. Rules vs classical models vs hybrid

Trained on `train.jsonl` (2,880 template messages). 95% bootstrap intervals in brackets.
Probe labels are silver (labelled by Claude, to be checked by the team).

## dev (template)

**Situation accuracy**

| System | English | Hindi | Hinglish | Marathi | All |
|---|---|---|---|---|---|
| rules | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] |
| TF-IDF words + Naive Bayes | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] |
| TF-IDF words (1-2) + LR | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] |
| TF-IDF chars (2-5) + LR | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] |
| TF-IDF words + chars + LR | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] |
| hybrid: rules + model (argmax) | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] |
| hybrid: rules + model (P≥0.3) | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] |

**Emergency recall** (missed emergencies in brackets after the interval)

| System | English | Hindi | Hinglish | Marathi | All |
|---|---|---|---|---|---|
| rules | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |
| TF-IDF words + Naive Bayes | 0.97 [0.93–0.99] (4 missed) | 0.99 [0.97–1.00] (1 missed) | 0.97 [0.94–1.00] (3 missed) | 0.93 [0.87–0.97] (7 missed) | 0.96 [0.95–0.98] (15 missed) |
| TF-IDF words (1-2) + LR | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |
| TF-IDF chars (2-5) + LR | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |
| TF-IDF words + chars + LR | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |
| hybrid: rules + model (argmax) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |
| hybrid: rules + model (P≥0.3) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |

**False-alarm rate** (non-emergencies flagged as emergency)

| System | All |
|---|---|
| rules | 0.00 [0.00–0.00] |
| TF-IDF words + Naive Bayes | 0.00 [0.00–0.00] |
| TF-IDF words (1-2) + LR | 0.00 [0.00–0.00] |
| TF-IDF chars (2-5) + LR | 0.00 [0.00–0.00] |
| TF-IDF words + chars + LR | 0.00 [0.00–0.00] |
| hybrid: rules + model (argmax) | 0.00 [0.00–0.00] |
| hybrid: rules + model (P≥0.3) | 0.00 [0.00–0.00] |

## safety suite (team-written)

**Situation accuracy**

| System | English | Hindi | Hinglish | Marathi | All |
|---|---|---|---|---|---|
| rules | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] |
| TF-IDF words + Naive Bayes | 0.90 [0.77–1.00] | 0.88 [0.75–1.00] | 0.92 [0.80–1.00] | 0.71 [0.50–0.88] | 0.85 [0.78–0.91] |
| TF-IDF words (1-2) + LR | 0.90 [0.77–1.00] | 0.92 [0.79–1.00] | 0.92 [0.80–1.00] | 0.88 [0.71–1.00] | 0.90 [0.83–0.95] |
| TF-IDF chars (2-5) + LR | 0.83 [0.70–0.97] | 0.92 [0.79–1.00] | 0.92 [0.80–1.00] | 0.88 [0.75–1.00] | 0.88 [0.82–0.94] |
| TF-IDF words + chars + LR | 0.90 [0.77–1.00] | 0.92 [0.79–1.00] | 0.92 [0.80–1.00] | 0.88 [0.75–1.00] | 0.90 [0.84–0.96] |
| hybrid: rules + model (argmax) | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] |
| hybrid: rules + model (P≥0.3) | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] | 1.00 [1.00–1.00] |

**Emergency recall** (missed emergencies in brackets after the interval)

| System | English | Hindi | Hinglish | Marathi | All |
|---|---|---|---|---|---|
| rules | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |
| TF-IDF words + Naive Bayes | 0.96 [0.88–1.00] (1 missed) | 0.90 [0.75–1.00] (2 missed) | 0.85 [0.65–1.00] (3 missed) | 0.80 [0.60–0.95] (4 missed) | 0.88 [0.81–0.94] (10 missed) |
| TF-IDF words (1-2) + LR | 0.96 [0.88–1.00] (1 missed) | 0.95 [0.85–1.00] (1 missed) | 0.90 [0.75–1.00] (2 missed) | 0.90 [0.75–1.00] (2 missed) | 0.93 [0.87–0.98] (6 missed) |
| TF-IDF chars (2-5) + LR | 0.96 [0.88–1.00] (1 missed) | 0.85 [0.65–1.00] (3 missed) | 0.90 [0.75–1.00] (2 missed) | 0.90 [0.75–1.00] (2 missed) | 0.91 [0.84–0.96] (8 missed) |
| TF-IDF words + chars + LR | 0.96 [0.88–1.00] (1 missed) | 0.90 [0.75–1.00] (2 missed) | 0.95 [0.85–1.00] (1 missed) | 0.85 [0.65–1.00] (3 missed) | 0.92 [0.85–0.98] (7 missed) |
| hybrid: rules + model (argmax) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |
| hybrid: rules + model (P≥0.3) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |

**False-alarm rate** (non-emergencies flagged as emergency)

| System | All |
|---|---|
| rules | 0.00 [0.00–0.00] |
| TF-IDF words + Naive Bayes | 0.33 [0.11–0.56] |
| TF-IDF words (1-2) + LR | 0.39 [0.17–0.61] |
| TF-IDF chars (2-5) + LR | 0.44 [0.22–0.67] |
| TF-IDF words + chars + LR | 0.44 [0.22–0.67] |
| hybrid: rules + model (argmax) | 0.44 [0.22–0.67] |
| hybrid: rules + model (P≥0.3) | 0.44 [0.22–0.67] |

## probe (machine-drafted, silver labels)

**Situation accuracy**

| System | English | Hindi | Hinglish | Marathi | All |
|---|---|---|---|---|---|
| rules | 1.00 [1.00–1.00] | 0.95 [0.86–1.00] | 0.95 [0.86–1.00] | 0.95 [0.86–1.00] | 0.97 [0.92–1.00] |
| rules before probe fixes (33802b7) | 0.96 [0.87–1.00] | 0.91 [0.77–1.00] | 0.86 [0.68–1.00] | 0.91 [0.77–1.00] | 0.91 [0.84–0.97] |
| TF-IDF words + Naive Bayes | 0.96 [0.87–1.00] | 0.95 [0.86–1.00] | 0.95 [0.86–1.00] | 0.91 [0.77–1.00] | 0.94 [0.90–0.99] |
| TF-IDF words (1-2) + LR | 0.96 [0.87–1.00] | 1.00 [1.00–1.00] | 0.95 [0.86–1.00] | 0.91 [0.77–1.00] | 0.96 [0.91–0.99] |
| TF-IDF chars (2-5) + LR | 0.91 [0.78–1.00] | 0.91 [0.77–1.00] | 0.95 [0.86–1.00] | 0.86 [0.73–1.00] | 0.91 [0.85–0.97] |
| TF-IDF words + chars + LR | 0.91 [0.78–1.00] | 0.91 [0.77–1.00] | 0.95 [0.86–1.00] | 0.86 [0.73–1.00] | 0.91 [0.84–0.97] |
| hybrid: rules + model (argmax) | 1.00 [1.00–1.00] | 0.95 [0.86–1.00] | 0.95 [0.86–1.00] | 0.95 [0.86–1.00] | 0.97 [0.92–1.00] |
| hybrid: rules + model (P≥0.3) | 1.00 [1.00–1.00] | 0.95 [0.86–1.00] | 0.95 [0.86–1.00] | 0.95 [0.86–1.00] | 0.97 [0.92–1.00] |
| hybrid: rules before fixes + model | 0.96 [0.87–1.00] | 0.91 [0.77–1.00] | 0.86 [0.68–1.00] | 0.91 [0.77–1.00] | 0.91 [0.84–0.97] |

**Emergency recall** (missed emergencies in brackets after the interval)

| System | English | Hindi | Hinglish | Marathi | All |
|---|---|---|---|---|---|
| rules | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |
| rules before probe fixes (33802b7) | 0.94 [0.82–1.00] (1 missed) | 0.88 [0.69–1.00] (2 missed) | 0.81 [0.62–1.00] (3 missed) | 0.88 [0.69–1.00] (2 missed) | 0.88 [0.78–0.95] (8 missed) |
| TF-IDF words + Naive Bayes | 0.88 [0.71–1.00] (2 missed) | 0.88 [0.69–1.00] (2 missed) | 1.00 [1.00–1.00] (0 missed) | 0.75 [0.56–0.94] (4 missed) | 0.88 [0.78–0.95] (8 missed) |
| TF-IDF words (1-2) + LR | 0.94 [0.82–1.00] (1 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 0.94 [0.81–1.00] (1 missed) | 0.97 [0.92–1.00] (2 missed) |
| TF-IDF chars (2-5) + LR | 0.94 [0.82–1.00] (1 missed) | 0.94 [0.81–1.00] (1 missed) | 1.00 [1.00–1.00] (0 missed) | 0.94 [0.81–1.00] (1 missed) | 0.95 [0.89–1.00] (3 missed) |
| TF-IDF words + chars + LR | 0.94 [0.82–1.00] (1 missed) | 0.94 [0.81–1.00] (1 missed) | 1.00 [1.00–1.00] (0 missed) | 0.94 [0.81–1.00] (1 missed) | 0.95 [0.89–1.00] (3 missed) |
| hybrid: rules + model (argmax) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |
| hybrid: rules + model (P≥0.3) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |
| hybrid: rules before fixes + model | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) | 1.00 [1.00–1.00] (0 missed) |

**False-alarm rate** (non-emergencies flagged as emergency)

| System | All |
|---|---|
| rules | 0.00 [0.00–0.00] |
| rules before probe fixes (33802b7) | 0.00 [0.00–0.00] |
| TF-IDF words + Naive Bayes | 0.25 [0.10–0.45] |
| TF-IDF words (1-2) + LR | 0.50 [0.30–0.70] |
| TF-IDF chars (2-5) + LR | 0.40 [0.20–0.60] |
| TF-IDF words + chars + LR | 0.50 [0.30–0.70] |
| hybrid: rules + model (argmax) | 0.50 [0.30–0.70] |
| hybrid: rules + model (P≥0.3) | 0.50 [0.30–0.70] |
| hybrid: rules before fixes + model | 0.50 [0.30–0.70] |

