# E4. Corpus statistics and code-mixing

Vocab per 24 msgs = distinct words in 24 random messages (size-matched; mean of 50 draws). Distinct bigrams = share of word pairs that are unique. CMI = Code-Mixing Index (Das & Gambäck 2014), 0 = one language, 50 = evenly mixed.

| Set | Language | Messages | Distinct | Words/msg | Vocabulary | Vocab per 24 msgs | Distinct bigrams | CMI (mean) | Code-mixed msgs |
|---|---|---|---|---|---|---|---|---|---|
| train (template) | English | 720 | 720 | 11.0 | 135 | 87 | 0.064 | 0.0 | 0% |
| train (template) | Hindi | 720 | 720 | 9.9 | 107 | 80 | 0.044 | 0.0 | 0% |
| train (template) | Hinglish | 720 | 720 | 9.7 | 112 | 82 | 0.050 | 5.9 | 43% |
| train (template) | Marathi | 720 | 720 | 7.8 | 90 | 68 | 0.047 | 0.0 | 0% |
| dev (template) | English | 180 | 180 | 11.4 | 135 | 88 | 0.196 | 0.0 | 0% |
| dev (template) | Hindi | 180 | 180 | 9.9 | 106 | 82 | 0.155 | 0.0 | 0% |
| dev (template) | Hinglish | 180 | 180 | 9.7 | 112 | 84 | 0.172 | 6.0 | 46% |
| dev (template) | Marathi | 180 | 180 | 7.8 | 90 | 70 | 0.165 | 0.0 | 0% |
| safety suite | English | 30 | 30 | 7.6 | 129 | 109 | 0.904 | 0.0 | 0% |
| safety suite | Hindi | 24 | 24 | 6.6 | 99 | 99 | 0.903 | 0.0 | 0% |
| safety suite | Hinglish | 25 | 25 | 7.7 | 110 | 107 | 0.929 | 5.1 | 28% |
| safety suite | Marathi | 24 | 24 | 4.7 | 85 | 85 | 0.943 | 0.0 | 0% |
| probe | English | 25 | 25 | 5.2 | 93 | 90 | 0.962 | 0.0 | 0% |
| probe | Hindi | 25 | 25 | 5.4 | 87 | 85 | 0.955 | 0.0 | 0% |
| probe | Hinglish | 25 | 25 | 5.5 | 88 | 86 | 0.947 | 6.3 | 28% |
| probe | Marathi | 25 | 25 | 3.6 | 78 | 75 | 0.984 | 0.0 | 0% |

Template data repeats a few frames with different people and times, so its vocabulary and bigram variety are a fraction
of the safety suite and probe of the same size; this is why template scores do not predict real-world accuracy.

