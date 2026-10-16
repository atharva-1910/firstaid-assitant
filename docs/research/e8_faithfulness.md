# E8. Faithfulness of explanations (F4)

Emergency messages from the safety suite and probe that the model flags. Comprehensiveness = mean drop in P(emergency) after deleting the words; flip = alert disappears.

| Model | Words deleted | Comprehensiveness | Alerts that disappear |
|---|---|---|---|
| word model | top 1 attributed | 0.09 | 6% |
| word model | 1 random | 0.03 | 5% |
| word model | top 2 attributed | 0.18 | 18% |
| word model | 2 random | 0.02 | 4% |
| word model | top 3 attributed | 0.26 | 26% |
| word model | 3 random | 0.03 | 4% |
| word model | app's trigger words (F4) | 0.06 | 7% |
| character model | top 1 attributed | 0.05 | 4% |
| character model | 1 random | 0.01 | 1% |
| character model | top 2 attributed | 0.08 | 5% |
| character model | 2 random | 0.02 | 3% |
| character model | top 3 attributed | 0.13 | 9% |
| character model | 3 random | 0.03 | 4% |
| character model | app's trigger words (F4) | 0.06 | 5% |

Rules: deleting the app's own trigger words removes the rule alert in 84% of 139 messages (the rest still fire on other words). The word model's top word is one of the app's trigger words in 51% of messages (character model: 78%).
