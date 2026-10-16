# Multilingual First Aid Assistant

A source-cited procedure corpus and safety-first NLP pipeline that helps an untrained bystander help an **adult** until the ambulance arrives. You can type what happened in **English, Hindi, Hinglish or Marathi**. The app then:

1. raises an emergency alert when it is needed, and explains why,
2. warns about harmful home remedies,
3. asks one well-chosen question when it is unsure,
4. shows calm, verified steps one at a time, with a source chip on every step,
5. ends with a handover summary for the ambulance crew.

It covers five situations: unresponsive or unconscious, heart attack, choking, bites (snake, insect or scorpion, dog), and burns (fire and heat, chemical and acid, electrical). The emergency number is **112**.

> **Research demo, not medical advice.** Every first aid step comes from `backend/content/` and carries its source. All records are still `draft`. Each situation owner must check every item in [`docs/VERIFY.md`](docs/VERIFY.md) against the source PDF before any demo.

CCNLP Mini Project, MIT World Peace University, Pune. The full specification is in [`docs/specification.md`](docs/specification.md). For a guided tour of every folder, file and model, see [`docs/WALKTHROUGH.md`](docs/WALKTHROUGH.md).

---

## Quick start

You need Python 3.11+ and Node 18+.

**Backend** (one command after install):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend** (one command after install). In a second terminal:

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173  (proxies /api to :8000)
```

**Single-server demo.** Build the frontend once with `cd frontend && npm run build`. The backend then serves the built app at http://localhost:8000.

The app runs in **stub mode** by default (`MODEL_MODE=stub`). Every model has a rule-based stand-in, so it needs no GPU and downloads nothing. It makes no external API calls at runtime, and the fonts are bundled.

## Tests

```bash
cd backend && python -m pytest -q        # 438 tests: safety suite, negation, extraction, flows, content, API
cd frontend && npm test                  # 46 tests: contrast (WCAG AA), red-usage rule, i18n parity, screen flow
```

The safety suite (`backend/tests/safety_suite.jsonl`) currently has 103 cases: 30 English, 25 Hinglish, 24 Hindi and 24 Marathi. Every `must_be_emergency: true` case must return `urgency = emergency` in every language, with the Call 112 screen first. Language owners extend the suite to 50 cases per language.

Two more tests check the rules floor. A triage model that answers "home" cannot lower an emergency found by the rules, and a model can always raise urgency.

## How it works

```
message ─► normalise ─► language id ─► F1 extraction + F3 negation ─► safety rules floor + triage
        ─► situation (+ F2 question if unsure) ─► verified steps ─► screens ─► handover summary
```

| Piece | File | Owner |
|---|---|---|
| Normalise (Unicode, Devanagari digits, nukta, curly quotes) | `backend/app/normalize.py` | — |
| Language id: trained char n-gram model (script first, then classifier); word-list rules with `LANGID=rules` | `backend/app/models/ngram_langid.py`, `backend/scripts/train_langid.py` | — |
| Cross-language safety net: sibling-language pass that can only raise urgency | `backend/app/extract.py` (`extract_safe`) | — |
| **F1** detail extraction (slots of Section 8.3, typo-tolerant) | `backend/app/extract.py`, `content/lexicons/*.json` | Taneesha |
| **F2** clarifying question (information gain) and conversation memory | `backend/app/clarify.py`, `backend/app/memory.py` | Atharva |
| **F3** negation and uncertainty (3-token window, per-language direction) | `backend/app/negation.py` | Siddhi |
| **F4** explainable alert (the user's own words, original spelling) | `backend/app/explain.py` | Soham |
| Safety rules floor (Section 8.2) | `backend/app/safety_rules.py` | all |
| Harmful-action detection (myth set) | `backend/app/harmful.py`, `content/myths.jsonl` | language owners |
| Orchestration | `backend/app/pipeline.py` | — |
| Stub and real models behind the Section 12 interfaces | `backend/app/models/{stub,real}` | model owners |

**Visual aids on steps.** Some steps carry an `aid` that helps the user do exactly what the step says, with no new instructions:

| Aid | Steps |
|---|---|
| CPR rhythm (110 per minute, optional click) | CPR steps in `unresponsive` Path A |
| Countdown timer | 10 s breathing check (`unr_s3`); 20 min burn cooling (`burns_fire_s2`, `burns_chem_s4`); 15 min dog-bite wash (`bite_dog_s2`) |
| Count-up timer | Eye rinse "until help arrives" (`burns_chem_s5`) |
| 5 + 5 cycle counter with pictures | Choking back blows and abdominal thrusts (`ch_s6`) |
| Note the time | Snakebite time (`bite_snake_s6`), added to the top of the handover summary |

**Animations** show the movement itself for CPR compressions (`unr_a4`, at the same 110-per-minute rate as the pacer), back blows (`ch_s4`) and abdominal thrusts (`ch_s5`); the choking counter plays them too. They are SVG drawings animated with CSS (`frontend/public/steps/anim/`), with a "Show still picture" toggle, and they fall back to the still picture when the phone asks for reduced motion.

Timers keep running while the user moves between steps. A backend test checks that every timer's length and every count appears in the step's own English text. Steps also show pictures: Wikimedia Commons files where available, otherwise the team's own CC0 drawings (`docs/illustrations/`). All pictures are `verified: false` until the situation owner checks them.

**Voice in and out.**

- *Speaking:* the mic needs no language choice. Browser speech recognition has to be told a language before it starts, so it begins in Hindi, which copes best with all four, and sends the first few words to `POST /api/langid` (the trained char n-gram model). If the model is at least 85% sure the speaker is using another language, the recogniser restarts in that language and keeps what it already heard. It switches at most twice per session, and if the check fails (offline) it keeps listening. The text always lands in the box for the user to check; nothing is sent by voice alone.
- *Reading aloud:* a "Read steps aloud" toggle on the step screen reads each step and its warnings with the phone's own voices (`speechSynthesis`; Marathi falls back to a Hindi voice, Hinglish uses an Indian English voice). It then moves to the next step after 3 seconds, except on steps that take time (timers, CPR, the choking counter) and the last step, where it says "tap Done, next" and waits. The setting is remembered on the device.

**Safety design.**

- The rules always run, in both modes, and a model can only raise urgency.
- An uncertain safety fact, such as "I think he isn't breathing" or "pata nahi", triggers a question. "Call 112" stays visible while the question is open.
- The app asks at most 2 questions in a row. If it is still unsure, it shows Call 112 and does not guess steps.
- Step text is never generated. A Gemma 3 rephrasing would be shown only if mmBERT verifies it in both directions. In stub mode, rephrasing is disabled.

## Repository layout

```
backend/
  app/                 FastAPI app, pipeline, F1–F4, safety rules, stub + real models
  content/             situations/*.json (5 records), lexicons/, questions.json, myths.jsonl, schema/, strings.json
  data/queries/        train.jsonl, dev.jsonl (template-generated), test.jsonl (hand-written, empty)
  scripts/             generate_queries.py, evaluate.py, verify_report.py
  tests/               safety_suite.jsonl + pytest suites
frontend/
  src/screens/         Home, Question, Emergency, HarmfulWarning, Step, Summary, Child, OutOfScope, About
  src/components/      Header, Call112Button, EmergencyBanner, StepCard, DoNotBox, SourceChips, ProgressBar, CprRhythm, AnswerButtons
  src/i18n/            en.json, hi.json, hinglish.json, mr.json
  src/theme/tokens.ts  Section 14 colour and size tokens
training/              Colab notebooks: 01 BGE-M3, 02 Gemma 3, 03 mmBERT, 04 IndicBERT v2
docs/                  specification, VERIFY checklist, evaluation report, datasheet, real-mode guide
```

## Status against the Definition of Done (Section 19)

| Item | Status |
|---|---|
| Runs locally with one command each for frontend and backend | ✅ |
| Five situations and subtypes show cited steps | ✅ English. Step translations are pending for Hindi, Hinglish and Marathi; these screens show English with a "Translation pending" label (Section 0.6). |
| Hinglish input detected and handled | ✅ |
| "Call 112" on every screen; red used nowhere else | ✅ (enforced by a frontend test) |
| Safety suite passes at 100% in every language | ✅ on 103 seed cases. Language owners extend it to 50 per language. |
| Child, infant and out-of-scope handled safely | ✅ |
| Every [VERIFY] resolved, pages filled, electrical source gap closed | ⏳ Situation owners: see `docs/VERIFY.md` (68 steps open) |
| Records marked `team_checked`; disclaimer on home and about | ⏳ / ✅ |
| Evaluation report with every Section 17.2 metric per language | ⏳ The script is ready; it needs the hand-written `test.jsonl` and the trained models. |

## Decisions made while building (please review)

These choices were not fully fixed by the spec. Each one leans towards caution.

- **Unknown bite.** The bite is treated as a possible snakebite: it is an emergency, the snakebite steps are shown, and the app asks `q_bite_type` (Section 8.2).
- **"Not sure" about breathing.** This follows Path A (CPR), which is the cautious path.
- **"Collapsed", "fell" or "gir gaye".** These count as an emergency, and the app asks about responsiveness first.
- **Choking with an unknown cough strength.** The app asks `q_can_cough` before showing the steps.
- **Electrical steps 2 and 3.** These have no source yet, so they show a "Source not confirmed yet" chip. You can remove them if no source is found (Section 4.1).
- **Hinglish negation.** Negation runs on the romanised text with Hinglish cue words. It does not run after transliteration, because the Hinglish cue list would never match Devanagari text.
- **Stub language id.** It adds lexicon evidence to the Marathi marker words in the spec, so short Marathi messages are not read as Hindi.
- **UI strings.** The Section 15.1 strings are used exactly as written. Other Hindi, Hinglish and Marathi UI text is a draft that needs a native-speaker check. Step content, questions and myth reasons are **not** translated (Section 0.2 and 0.6).

## Research experiments

`backend/research/` holds eight experiments for the report: rules vs classical models vs the hybrid, cross-lingual
transfer, robustness to noise, corpus statistics and code-mixing, calibration, negation scope, an adversarial test for
the step verifier, and faithfulness of explanations. `python -m research.report` (from `backend/`) reruns all of them
in about 9 minutes and writes [`docs/research/README.md`](docs/research/README.md) with the main table and findings.
Transformer runs are in `training/05_research_transformers.ipynb` (Colab). Writing and labelling the hand-written
test sets: [`docs/annotation/GUIDELINES.md`](docs/annotation/GUIDELINES.md).

## Real models

See [`docs/REAL_MODE.md`](docs/REAL_MODE.md). In short: train with the notebooks in `training/`, install `backend/requirements-real.txt`, and set `MODEL_MODE=real`.

## Team

| Name | PRN | Language | Feature | Situation(s) | Model |
|---|---|---|---|---|---|
| Taneesha Badhe | 1032232190 | English | F1 extraction | Unresponsive, Heart attack | BGE-M3 |
| Atharva Hemade | 1032232249 | Hindi | F2 question + memory | Choking | Gemma 3 |
| Siddhi Karhekar | 1032232132 | Marathi | F3 negation | Bites | mmBERT |
| Soham Ghodake | 1032232337 | Hinglish | F4 explainable alert | Burns | IndicBERT v2 |

*Guidance is drawn from the IFRC International First Aid, Resuscitation and Education Guidelines 2025; the 2024 AHA and American Red Cross Guidelines for First Aid; the 2025 AHA Guidelines for CPR and ECC; the 2025 ILCOR International Consensus on First Aid Science; and India's National Action Plan for Prevention and Control of Snakebite Envenoming. In an emergency, call 112.*
