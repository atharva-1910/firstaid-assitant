# E5. Calibration and selective prediction

ECE = expected calibration error (lower is better). AURC = area under the risk-coverage curve (lower is better).
At 0.75: share of messages answered without a question at the app's threshold, and accuracy on those vs on the rest.

| Set | Confidence from | Accuracy | ECE | AURC | Answered at 0.75 | Acc. answered | Acc. would-ask |
|---|---|---|---|---|---|---|---|
| dev (template) | model | 1.00 | 0.015 | 0.000 | 100% | 1.00 | – |
| dev (template) | rules (app confidence) | 1.00 | 0.090 | 0.000 | 100% | 1.00 | – |
| safety suite + probe | model | 0.91 | 0.051 | 0.040 | 84% | 0.96 | 0.63 |
| safety suite + probe | rules (app confidence) | 0.98 | 0.096 | 0.000 | 96% | 1.00 | 0.62 |

In the app (dev (template)): a question was asked for 16% of messages; accuracy on the rest was 1.00.

In the app (safety suite + probe): a question was asked for 27% of messages; accuracy on the rest was 1.00.
