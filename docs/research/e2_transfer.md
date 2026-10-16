# E2. Cross-lingual transfer (English + a fraction of the target language)

Situation accuracy on the target language, mean over 3 subsamples. Classical features cannot cross scripts,
so 0% for Hindi and Marathi is a floor, not zero-shot transfer; the Colab notebook runs the same curve with multilingual embeddings.

**TF-IDF chars (2-5) + LR · dev (template)**

| Target | 0% | 5% | 10% | 25% | 50% | 100% |
|---|---|---|---|---|---|---|
| Hindi | 0.26 | 0.91 | 0.98 | 1.00 | 1.00 | 1.00 |
| Hinglish | 0.24 | 0.81 | 0.96 | 1.00 | 1.00 | 1.00 |
| Marathi | 0.23 | 0.92 | 0.98 | 1.00 | 1.00 | 1.00 |

**TF-IDF chars (2-5) + LR · probe**

| Target | 0% | 5% | 10% | 25% | 50% | 100% |
|---|---|---|---|---|---|---|
| Hindi | 0.00 | 0.88 | 0.89 | 0.91 | 0.91 | 0.91 |
| Hinglish | 0.45 | 0.86 | 0.91 | 0.95 | 0.95 | 0.95 |
| Marathi | 0.00 | 0.82 | 0.82 | 0.86 | 0.86 | 0.86 |

**TF-IDF words (1-2) + LR · dev (template)**

| Target | 0% | 5% | 10% | 25% | 50% | 100% |
|---|---|---|---|---|---|---|
| Hindi | 0.13 | 0.90 | 0.96 | 1.00 | 1.00 | 1.00 |
| Hinglish | 0.22 | 0.85 | 0.96 | 1.00 | 1.00 | 1.00 |
| Marathi | 0.16 | 0.90 | 0.98 | 1.00 | 1.00 | 1.00 |

**TF-IDF words (1-2) + LR · probe**

| Target | 0% | 5% | 10% | 25% | 50% | 100% |
|---|---|---|---|---|---|---|
| Hindi | 0.27 | 0.79 | 0.88 | 0.98 | 1.00 | 1.00 |
| Hinglish | 0.32 | 0.77 | 0.88 | 0.94 | 0.95 | 0.95 |
| Marathi | 0.27 | 0.82 | 0.89 | 0.91 | 0.91 | 0.91 |

