# Query set (Section 10)

| File | Contents | Who writes it |
|---|---|---|
| `train.jsonl` | Template queries, 120 per class per language (default) | `python scripts/generate_queries.py` |
| `dev.jsonl` | Template queries, 30 per class per language | same script (20% held out) |
| `test.jsonl` | **Hand-written** queries, 50 per class per language (300 per language) | each language owner |

Rules (Section 10.3):

- Gold labels come from the templates and the language owner, never from a paraphrasing model.
- Hinglish test queries are written by hand in natural romanised spelling, including common misspellings; they are not transliterated from Hindi.
- Test queries are never used for training, for tuning, or as prompt examples.

`test.jsonl` is empty on purpose. Add one JSON object per line:

```json
{"id": "hg-bite-0042", "lang": "hinglish", "text": "khet mein saap ne kaat liya pair pe, kya karu", "situation": "bites", "subtype": "snake", "urgency": "emergency", "slots": {"age_group": "adult", "bite_type": "snake"}, "split": "test", "written_by": "human"}
```

`situation` is one of `unresponsive`, `heart_attack`, `choking`, `bites`, `burns`, `out_of_scope` (child and infant cases count as out of scope).
`subtype` is `path_a` / `path_b` for unresponsive, the bite type for bites (`snake`, `insect_sting`, `scorpion`, `dog`), the branch for burns (`fire_heat`, `chemical_acid`, `electrical`), otherwise `null`.

Run the evaluation with `python scripts/evaluate.py --baselines --out ../docs/evaluation_report.md`. It uses `test.jsonl` when it has rows, otherwise `dev.jsonl`.
