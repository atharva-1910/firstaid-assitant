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

## Language identification: word-list rules vs trained char n-gram model

Model: TF-IDF over character 1–4-grams inside words, multinomial logistic regression (C = 10), 9,489 features, 481 KB of JSON weights, pure-Python inference. The script decides first (Devanagari → hi/mr, Latin → en/hinglish), and the classifier picks within that pair. Trained on `train.jsonl` plus every translated sentence in `content/` and the UI strings. Reproduce with `python scripts/train_langid.py`.

| Set | Method | en | hi | hinglish | mr | Overall |
|---|---|---|---|---|---|---|
| dev (templates) | word-list rules | 180/180 | 180/180 | 178/180 | 180/180 | 0.997 |
| dev (templates) | char n-gram model | 180/180 | 180/180 | 180/180 | 180/180 | 1.000 |
| safety suite | word-list rules | 30/30 | 24/24 | 25/25 | 24/24 | 1.000 |
| safety suite | char n-gram model | 30/30 | 24/24 | 25/25 | 24/24 | 1.000 |
| probe (harder, hand-written) | word-list rules | 25/25 | 25/25 | 23/25 | 24/25 | 0.970 |
| probe (harder, hand-written) | char n-gram model | 25/25 | 25/25 | 25/25 | 25/25 | 1.000 |

The probe set (`data/queries/langid_probe.jsonl`, 100 messages) is short, misspelt and code-mixed on purpose, and is never used for training. It was drafted by the build tool, not by the language owners, so it is a sanity check rather than the Section 10 test set. Rule errors on it: "dadaji ko current laga 10 minute pehle" → en, "tatiya ne kaata" → en, "लवकर सांगा" → hi.

**Cross-language safety net.** Extraction also runs with the sibling language of the same script (hi↔mr, en↔hinglish) and keeps only facts that raise urgency, from words the main pass did not already read. With the language deliberately forced wrong on every safety-suite emergency, missed emergencies fall from 55/85 to 0/85, with 0/18 false alarms (right or wrong language). Two sting phrasings (Hindi डंक vs Marathi डंख) were missed until each spelling was added to the other lexicon.

**Lexicon gaps found by the probe set.** Before the fix, emergency recall on the probe set was 0.92 (en), 0.85 (hi), 0.77 (hinglish), 0.85 (mr). Every miss was a missing phrasing: "breath stopped" (saans ruk gayi, साँस रुक गई, श्वास थांबला) and a heavy or tight chest (chest heavy, सीना भारी, छाती जड). After adding them (with regression tests in `tests/test_extract.py`), probe recall is 1.00 in every language. Because the fix was chosen from probe errors, the probe set is no longer an unseen test; the hand-written `test.jsonl` remains the fair measure.
