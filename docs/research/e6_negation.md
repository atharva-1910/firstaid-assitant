# E6. Negation and uncertainty (F3)

Fact-level accuracy (each sentence states 1–2 facts). Dangerous = a negated or uncertain fact read as reassuring.

## diagnostic (machine-drafted)

| Variant | English | Hindi | Hinglish | Marathi | All | Dangerous errors |
|---|---|---|---|---|---|---|
| current (3 tokens, language direction) | 0.90 | 0.81 | 0.81 | 0.89 | 0.85 | 9 |
| no direction preference | 0.90 | 0.81 | 0.81 | 0.89 | 0.85 | 9 |
| English rule (cue before word only) | 0.90 | 0.62 | 0.62 | 0.64 | 0.70 | 78 |
| window 1 | 0.78 | 0.75 | 0.81 | 0.82 | 0.79 | 34 |
| window 6 | 0.90 | 0.81 | 0.81 | 0.89 | 0.85 | 4 |
| ConText-style (whole clause) | 0.94 | 0.81 | 0.81 | 0.88 | 0.86 | 0 |
| proposed: current + clause-wide uncertainty | 1.00 | 0.94 | 0.94 | 0.94 | 0.95 | 0 |

**Current rule, by frame** (accuracy)

| Frame | Kind | English | Hindi | Hinglish | Marathi |
|---|---|---|---|---|---|
| F01 | affirmed | 1.00 | 1.00 | 1.00 | 1.00 |
| F02 | negated | 1.00 | 1.00 | 1.00 | 1.00 |
| F03 | uncertain | 0.20 | 0.00 | 0.00 | 0.20 |
| F04 | negated | 1.00 | 1.00 | 1.00 | 1.00 |
| F05 | affirmed | 1.00 | 1.00 | 1.00 | 1.00 |
| F06 | affirmed | 1.00 | 1.00 | 1.00 | 1.00 |
| F07 | negated | 1.00 | 1.00 | 1.00 | 1.00 |
| F08 | negated, long scope | 1.00 | 0.00 | 0.00 | 0.00 |
| F09 | two facts, with breaker | 1.00 | 1.00 | 1.00 | 1.00 |
| F10 | two facts, negated first | 1.00 | 1.00 | 1.00 | 1.00 |
| F11 | two facts, negated second | 1.00 | 1.00 | 1.00 | 1.00 |
| F12 | negated, cue 2-3 words away | 1.00 | 1.00 | 1.00 | 1.00 |
| F13 | uncertain ("not sure if") | 0.20 | 0.00 | 0.00 | 1.00 |

