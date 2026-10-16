# E3. Robustness to noise

Mean over 3 noise seeds (safety suite + probe) or 1 seed (dev sample). Level = chance that each word is changed.

**Emergency recall at level 0.3 · safety suite + probe**

| Noise | rules | model (chars) | model (words) | hybrid (rules + chars model) |
|---|---|---|---|---|
| vowel_drop | 0.61 | 0.92 | 0.96 | 0.97 |
| typos | 0.78 | 0.93 | 0.95 | 0.99 |
| spelling | 0.91 | 0.93 | 0.95 | 1.00 |
| code_switch | 0.75 | 0.96 | 0.96 | 0.99 |
| fragment | 0.60 | 0.93 | 0.96 | 0.97 |
| all combined | 0.24 | 0.96 | 0.97 | 0.97 |

**False-alarm rate at level 0.3 · safety suite + probe**

| Noise | rules | model (chars) | model (words) | hybrid (rules + chars model) |
|---|---|---|---|---|
| vowel_drop | 0.11 | 0.48 | 0.53 | 0.53 |
| typos | 0.04 | 0.46 | 0.50 | 0.49 |
| spelling | 0.07 | 0.41 | 0.45 | 0.46 |
| code_switch | 0.11 | 0.36 | 0.52 | 0.45 |
| fragment | 0.11 | 0.47 | 0.55 | 0.52 |
| all combined | 0.13 | 0.56 | 0.73 | 0.62 |

**Situation accuracy at level 0.3 · safety suite + probe**

| Noise | rules | model (chars) | model (words) | hybrid (rules + chars model) |
|---|---|---|---|---|
| vowel_drop | 0.75 | 0.85 | 0.83 | 0.75 |
| typos | 0.87 | 0.88 | 0.89 | 0.87 |
| spelling | 0.94 | 0.90 | 0.92 | 0.94 |
| code_switch | 0.83 | 0.90 | 0.88 | 0.83 |
| fragment | 0.74 | 0.82 | 0.81 | 0.74 |
| all combined | 0.50 | 0.76 | 0.65 | 0.50 |

**All noise combined, by level · safety suite + probe** (emergency recall / situation accuracy)

| Level | rules | model (chars) | model (words) | hybrid (rules + chars model) |
|---|---|---|---|---|
| 0.0 | 1.00 / 0.98 | 0.93 / 0.90 | 0.95 / 0.93 | 1.00 / 0.98 |
| 0.1 | 0.64 / 0.79 | 0.94 / 0.87 | 0.95 / 0.83 | 0.98 / 0.79 |
| 0.2 | 0.42 / 0.61 | 0.96 / 0.80 | 0.96 / 0.77 | 0.98 / 0.61 |
| 0.3 | 0.24 / 0.50 | 0.96 / 0.76 | 0.97 / 0.65 | 0.97 / 0.50 |
| 0.5 | 0.10 / 0.35 | 0.99 / 0.66 | 0.98 / 0.52 | 0.99 / 0.35 |

**Emergency recall at level 0.3 · dev sample (template)**

| Noise | rules | model (chars) | model (words) | hybrid (rules + chars model) |
|---|---|---|---|---|
| vowel_drop | 0.60 | 1.00 | 0.99 | 1.00 |
| typos | 0.78 | 1.00 | 1.00 | 1.00 |
| spelling | 0.85 | 1.00 | 1.00 | 1.00 |
| code_switch | 0.76 | 1.00 | 0.99 | 1.00 |
| fragment | 0.57 | 1.00 | 0.99 | 1.00 |
| all combined | 0.17 | 1.00 | 1.00 | 1.00 |

**False-alarm rate at level 0.3 · dev sample (template)**

| Noise | rules | model (chars) | model (words) | hybrid (rules + chars model) |
|---|---|---|---|---|
| vowel_drop | 0.10 | 0.07 | 0.05 | 0.12 |
| typos | 0.03 | 0.00 | 0.03 | 0.03 |
| spelling | 0.15 | 0.00 | 0.00 | 0.15 |
| code_switch | 0.15 | 0.03 | 0.07 | 0.15 |
| fragment | 0.07 | 0.15 | 0.25 | 0.17 |
| all combined | 0.17 | 0.42 | 0.53 | 0.53 |

**Situation accuracy at level 0.3 · dev sample (template)**

| Noise | rules | model (chars) | model (words) | hybrid (rules + chars model) |
|---|---|---|---|---|
| vowel_drop | 0.79 | 0.99 | 0.98 | 0.79 |
| typos | 0.88 | 1.00 | 0.99 | 0.88 |
| spelling | 0.95 | 1.00 | 1.00 | 0.95 |
| code_switch | 0.80 | 0.98 | 1.00 | 0.80 |
| fragment | 0.76 | 0.98 | 0.97 | 0.76 |
| all combined | 0.39 | 0.90 | 0.82 | 0.39 |

**All noise combined, by level · dev sample (template)** (emergency recall / situation accuracy)

| Level | rules | model (chars) | model (words) | hybrid (rules + chars model) |
|---|---|---|---|---|
| 0.0 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 | 1.00 / 1.00 |
| 0.1 | 0.63 / 0.78 | 1.00 / 0.99 | 0.99 / 0.99 | 1.00 / 0.78 |
| 0.2 | 0.36 / 0.59 | 1.00 / 0.98 | 0.99 / 0.94 | 1.00 / 0.59 |
| 0.3 | 0.17 / 0.39 | 1.00 / 0.90 | 1.00 / 0.82 | 1.00 / 0.39 |
| 0.5 | 0.07 / 0.28 | 1.00 / 0.75 | 0.99 / 0.60 | 1.00 / 0.28 |

