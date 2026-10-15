# Datasheet

## Procedure corpus (`backend/content/situations/*.json`)

- **What.** Five adult first aid procedures stored as step graphs. Each record has recognition signs, branching steps, do-not rules with reasons, urgency rules, and a source citation on every step.
- **Sources.** Only post-2020 guidelines (Section 4.1): IFRC 2025 (G1), AHA/Red Cross 2024 (G2), AHA BLS 2025 (G3), ILCOR 2025 (G4) and NAPSE 2024 (G5).
- **Wording.** The steps are the team's own words, copied verbatim from Section 9 of the specification. Steps marked "(checked)" in the spec have `source.quote_checked: true`.
- **Status.** All records are `draft`. G1 page numbers are section start pages taken from the table of contents. `agreement` and `evidence` are `unchecked`. See `docs/VERIFY.md`.
- **Validation.** `content/schema/situation.schema.json` rejects any step that has no `source.doc`. The loader also checks that every `next` pointer and every do-not step reference exists.
- **Languages.** English is complete. Hindi, Hinglish and Marathi fields are empty until the language owners translate and check them; the app shows English with a "Translation pending" label.

## Lexicons (`backend/content/lexicons/{lang}.json`)

Pattern lists that drive F1 extraction and the stub models. Each entry has terms, the slots it sets when affirmed, the slots it sets when negated, flags, and the situations it is evidence for. The lists also hold negation and uncertainty cues, scope breakers, age and time units, and markers for language identification. The Hinglish lexicon includes the English one, because Hinglish mixes the two.

## Myth set (`backend/content/myths.jsonl`)

There are 13 seed items from Section 9.6, each with match patterns in all four languages and the reason shown to the user. The three snakebite items are checked against G5; the rest are still marked for verification. The target is about 40 items per language.

## Query set (`backend/data/queries/`)

- `train.jsonl` and `dev.jsonl` are generated from templates by `scripts/generate_queries.py`: 150 queries per class per language, split 80/20, 3,600 in total. Gold labels come from the templates.
- `test.jsonl` will hold the hand-written queries: 50 per class per language, 1,200 in total. Each language owner writes theirs. It is empty for now.

## Safety suite (`backend/tests/safety_suite.jsonl`)

There are 103 seed cases (en 30, hinglish 25, hi 24, mr 24). Each case has `must_be_emergency` and the expected screen or situation. The target is 50 per language. The suite runs on every build.

## Known limitations

- The template data is easy for the stub. Real accuracy must be measured on the hand-written test set.
- The stub language id is a heuristic. Very short or mixed messages can be misread; the user can always switch the language in the header.
- Lexicon coverage decides recall in stub mode. A missing phrase means a missed fact, so language owners should grow the lexicons from real queries.
