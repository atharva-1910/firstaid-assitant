# Repository walkthrough

A guide to everything in this repository: what each folder and file does, every model the project uses or
plans to use, and where each one lives. Read this first if you are new to the code.

**The project in one line.** A web app that helps an untrained bystander give first aid to an adult in five
situations (unresponsive, heart attack, choking, bites, burns). People describe the emergency in English, Hindi,
Hinglish or Marathi, by typing or speaking. The app raises an alert when needed, asks at most two questions, then
shows verified, source-cited steps one at a time. It never generates medical text: every step comes from the
content files.

**Live demo:** https://firstaid-assistant.onrender.com (free tier; the first visit after a quiet spell takes about a minute).

---

## 1. Top-level map

| Path | What it is |
|---|---|
| `backend/` | Python FastAPI server: the NLP pipeline, the first aid content, data sets, tests and research experiments |
| `frontend/` | React + TypeScript web app (Vite, Tailwind): every screen the user sees |
| `training/` | Colab notebooks that fine-tune the transformer models (not yet run) |
| `docs/` | Specification, evaluation and research results, annotation kit, CCA1 report, illustration sources |
| `Dockerfile`, `.dockerignore` | Builds one container: compiles the frontend, then serves it from the backend |
| `render.yaml` | Render blueprint for the free deployment (one Docker web service, stub mode) |
| `.env.example` | Settings: `MODEL_MODE` (stub or real), `LANGID`, model paths, Ollama URL, CORS |
| `README.md` | Quick start, tests and the pipeline overview |

**Run it locally** (Python 3.11+ and Node 18+):

```bash
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --port 8000
cd frontend && npm install && npm run dev   # http://localhost:5173
```

---

## 2. How one message flows through the system

```
message → normalise → language id → F1 extraction + F3 negation (+ cross-language safety net)
        → safety rules floor + triage → situation (+ F2 question if unsure) → verified steps → screens → handover summary
```

The safety rules always run. A model can only make the system **more** cautious, never less.

---

## 3. Backend (`backend/`)

### 3.1 `app/`: the server and the pipeline

| File | What it does | Owner |
|---|---|---|
| `main.py` | FastAPI routes: `POST /api/analyze` (a message), `POST /api/answer` (a question answer), `POST /api/langid` (used by the mic), `GET /api/situations/{id}`, `POST /api/summary`, `GET /api/health`. Also serves the built frontend. | all |
| `pipeline.py` | Orchestrates every step above; decides the next screen; renders steps, do-not boxes, images, animations, Yes/No checks and step aids | all |
| `config.py` | Reads `.env`: model mode, language-id choice, model paths, CORS | all |
| `normalize.py` | Unicode clean-up, Devanagari digits → 0–9, nukta and quote fixes, tokenising | all |
| `lexicon.py` | Compiles the per-language word lists into fast, typo-tolerant matchers (rapidfuzz) | all |
| `extract.py` | **F1** detail extraction: fills 12 slots (responsive, breathing, chest pain, choking signs, bite type, allergy, burn cause/area, power, age, time, actions). Also `extract_safe`, the cross-language safety net | Taneesha |
| `negation.py` | **F3** negation and uncertainty: attaches cues ("nahi", "नाही", "not sure") to the nearest symptom within 3 tokens, in each language's direction | Siddhi |
| `clarify.py` | **F2** picks the clarifying question with the highest information gain; safety questions win | Atharva |
| `memory.py` | **F2** per-session memory of facts (expires after 2 hours) | Atharva |
| `safety_rules.py` | The rules floor (19 rules): unresponsive, abnormal breathing, chest pain, snakebite, electrical injury and so on force an emergency | Soham |
| `explain.py` | **F4** "Why this alert?": the user's own trigger words, in their original spelling | Soham |
| `harmful.py` | Detects harmful home remedies (tourniquet, toothpaste on a burn…) from `content/myths.jsonl` | language owners |
| `summary.py` | Handover summary for the ambulance crew, built only from what the user said | all |
| `urgency.py` | The three urgency levels and their order | all |
| `content.py` | Loads and validates all content; English fallback with a "translation pending" label | all |
| `models/` | The model layer (see Section 7): `stub/` rule-based stand-ins, `real/` transformer versions, `ngram_langid.py` the trained language model, `weights/langid_charngram.json` its weights, `base.py` the shared interfaces | all |

### 3.2 `content/`: all first aid text (the only source of what users read)

| File | Contents |
|---|---|
| `situations/*.json` | Five procedure records, 68 steps. Each step has its source (IFRC 2025, AHA 2024/2025, ILCOR 2025 or NAPSE), page, agreement and evidence labels, translations in four languages, optional image, animation, step aid and Yes/No check. All still `draft` until verified. |
| `questions.json` | The 9 clarifying questions with answers in four languages and the facts each answer sets |
| `lexicons/{en,hi,hinglish,mr}.json` | Word lists per language: symptom phrases, negation and uncertainty cues, marker words, actions, age and time units |
| `myths.jsonl` | 13 harmful remedies with the reason each is harmful |
| `strings.json` | Backend-built text (disclaimer, summary lines) in four languages |
| `schema/situation.schema.json` | JSON Schema that rejects any step without a source |

### 3.3 `data/`: data sets

| File | Size | Use |
|---|---|---|
| `queries/train.jsonl` | 2,880 | Template messages (720 per language), labelled with situation, subtype, urgency and slots; trains models |
| `queries/dev.jsonl` | 720 | Template development set |
| `queries/test.jsonl` | 0 | **The hand-written test set: to be written by the team** (see `docs/annotation/`) |
| `queries/langid_probe.jsonl` | 100 | Short, misspelt, code-mixed messages for language-id checks |
| `queries/probe_labelled.jsonl` | 100 | The same messages with silver situation and urgency labels for the research experiments |
| `verifier/adversarial.jsonl` | 1,309 | Step pairs (safe rewording vs dangerous edit) for testing the step verifier |

### 3.4 `tests/`: 461 tests, all passing

`safety_suite.jsonl` holds 103 must-pass cases (85 must be emergencies) in four languages. `test_safety.py` runs
them and checks that a model can never lower an emergency; `test_negation.py`, `test_extract.py`,
`test_langid.py`, `test_flows.py`, `test_content.py` and `test_api.py` cover the rest. Run `python -m pytest -q`.

### 3.5 `scripts/`

| Script | What it does |
|---|---|
| `generate_queries.py` | Builds `train.jsonl` and `dev.jsonl` from templates |
| `train_langid.py` | Trains the character n-gram language model and compares it with the word lists |
| `evaluate.py` | Per-language evaluation, safety measures first; writes `docs/evaluation_report.md` |
| `verify_report.py` | Lists every `[VERIFY]` item the situation owners must check; writes `docs/VERIFY.md` |

### 3.6 `research/`: experiments E1–E8 (CPU, scikit-learn)

Run all with `python -m research.report` (about 9 minutes); results land in `docs/research/`.

| Experiment | Question | Owner |
|---|---|---|
| `e1_models.py` | Rules vs classical models vs the rules + model hybrid | all |
| `e2_transfer.py` | How much Hindi/Hinglish/Marathi data is needed on top of English? | Taneesha |
| `e3_robustness.py` | How do rules and models hold up under typos, dropped vowels and code-switching? (`noise.py`) | all |
| `e4_corpus.py` | Corpus statistics and the Code-Mixing Index | all |
| `e5_calibration.py` | Is the 0.75 "ask a question" threshold well placed? | Atharva |
| `e6_negation.py` | Negation window and direction against alternatives (`negation_frames.py`) | Siddhi |
| `e7_verifier.py` | Can a verifier catch dangerous rewordings? | Siddhi |
| `e8_faithfulness.py` | Are the highlighted alert words really the cause? | Soham |

`common.py` and `plotting.py` are shared helpers; `annotation.py` creates and imports the hand-written test sheets
and computes Cohen's kappa; `make_notebook.py` writes notebook 05; `report*.py` write the summaries and figures.

### 3.7 Requirements files

`requirements.txt` (runtime, stub mode), `requirements-offline.txt` (data tools), `requirements-research.txt`
(experiments), `requirements-real.txt` (transformers, PyTorch, for real mode).

---

## 4. Frontend (`frontend/`)

| Path | What it does |
|---|---|
| `src/App.tsx`, `src/flow.ts` | Screen flow: which screen comes next, and the step queue |
| `src/screens/` | The nine screens: Home, Question, Emergency, HarmfulWarning, Step, Summary, Child, OutOfScope, About |
| `src/components/` | Header with the red Call 112 pill, step card (picture or animation), do-not box, source chips, progress bar, CPR rhythm circle (110 per minute), answer buttons |
| `src/components/aids/` | Step aids: countdown timers (10 s breathing check, 15 min wound washing, 20 min burn cooling), a stopwatch (eye rinsing), the back-blow / abdominal-thrust cycle counter and "note the time" (snakebite) |
| `src/speech.ts` | Mic input: browser speech recognition that starts in Hindi, asks `/api/langid` which language it heard, and switches recogniser if needed. Never submits on its own |
| `src/tts.ts` | Read-aloud for steps with the phone's own voices |
| `src/i18n/` | All UI text in English, Hindi, Hinglish and Marathi |
| `src/theme/tokens.ts` | Design tokens: colours (red only for emergency actions), sizes |
| `src/api/client.ts` | Typed API calls and response types |
| `src/sources.ts` | Guideline names and links for the source chips |
| `src/__tests__/` | 64 tests: flow, i18n parity, WCAG contrast, red-usage rule, speech, read-aloud, step aids, Yes/No checks, images |
| `public/steps/*.webp` | Step pictures: five from Wikimedia Commons (CC BY-SA 4.0 / CC0), eight drawn by the team (CC0) |
| `public/steps/anim/*.svg` | Animations: CPR pushes, back blows, abdominal thrusts |

---

## 5. Training notebooks (`training/`)

Run on Google Colab with a GPU. Outputs go to `training/out/` (git-ignored) and are loaded in real mode.

| Notebook | Trains | Owner |
|---|---|---|
| `01_situation_bge_m3.ipynb` | BGE-M3 embeddings + classifier for the situation | Taneesha |
| `02_rephrase_gemma3.ipynb` | Gemma 3 4B step rephrasing, filtered by the verifier | Atharva |
| `03_verifier_mmbert.ipynb` | mmBERT entailment model on XNLI + IndicXNLI | Siddhi |
| `04_triage_indicbert.ipynb` | IndicBERT v2 urgency triage, MuRIL as the Hinglish comparison | Soham |
| `05_research_transformers.ipynb` | Transformer rows for the research experiments (LaBSE, BGE-M3, multilingual-E5, IndicBERT v2, MuRIL) | all |

---

## 6. Documentation (`docs/`)

| Path | Contents |
|---|---|
| `specification.md` | The full build specification (binding) |
| `REAL_MODE.md` | How to switch from stub to real models |
| `VERIFY.md` | Checklist of every step to verify against the source PDFs |
| `datasheet.md` | Datasheet for the corpora |
| `evaluation_report.md` | Per-language results, language-id comparison, safety-net and probe findings |
| `research/` | Results of E1–E8 (`README.md` summary, one page and JSON file per experiment, `references.md`) |
| `annotation/` | `GUIDELINES.md` and blank CSV sheets for writing the hand-written test sets and negation sets |
| `report/` | The CCA1 report (`CCA1_Report_FirstAid_Assistant.docx`), its build scripts and figures |
| `illustrations/` | Python sources (`src/`) and SVGs for the team's own step pictures |
| `WALKTHROUGH.md` | This file |

---

## 7. Every model, its status and where it lives

The app runs in **stub mode** by default: every NLP component has a light stand-in behind the same interface,
so it runs on a laptop CPU with no downloads. Real mode swaps in the transformers once they are trained.

### 7.1 Models running in the deployed app (stub mode)

| Component | Model | Status | Code | Weights / data |
|---|---|---|---|---|
| Language identification | **Character n-gram TF-IDF + logistic regression** (1–4-grams, 9,489 features); English written in Devanagari is detected separately | **Trained, in use** | `backend/app/models/ngram_langid.py` | `backend/app/models/weights/langid_charngram.json` (481 KB), trained by `scripts/train_langid.py` |
| Urgency triage | Safety rules from the word lists | In use | `app/models/stub/`, `app/safety_rules.py` | `content/lexicons/` |
| Situation identification | Keyword-overlap scores | In use | `app/models/stub/` | `content/lexicons/` |
| Step verifier | Always rejects rephrasing, so users see verified text only | In use | `app/models/stub/` | none |
| Rephraser | Disabled | — | `app/models/stub/` | none |
| Explanation (F4) | Rule trigger words | In use | `app/explain.py` | none |
| Speech to text | Browser Web Speech API (Google in Chrome, Apple in Safari) | In use, in the browser | `frontend/src/speech.ts` | not ours |
| Read-aloud | Browser `speechSynthesis` voices | In use, in the browser | `frontend/src/tts.ts` | not ours |

### 7.2 Transformer models (real mode, notebooks ready, not yet trained)

| Component | Model | Hugging Face id | Notebook | Loaded from | Owner |
|---|---|---|---|---|---|
| Situation | BGE-M3 (2024) | `BAAI/bge-m3` | 01 | Hub | Taneesha |
| Rephrasing (optional) | Gemma 3 4B (2025) | `google/gemma-3-4b-it`, or `gemma3:4b` via Ollama | 02 | `OLLAMA_URL` | Atharva |
| Step verifier | mmBERT (2025), fine-tuned | `jhu-clsp/mmBERT-base` | 03 | `training/out/mmbert_verifier` | Siddhi |
| Triage | IndicBERT v2 (2023), fine-tuned | `ai4bharat/IndicBERTv2-MLM-only` | 04 | `training/out/indicbert_triage` | Soham |
| Hinglish comparison | MuRIL (2021) | `google/muril-base-cased` | 04, 05 | — | Soham |
| Language id (real mode) | IndicLID (AI4Bharat, 2023) | AI4Bharat install | — | falls back to the n-gram model | — |
| Explanation (real mode) | transformers-interpret on the triage model | — | 05 | — | Soham |
| Research embeddings | LaBSE, multilingual-E5 | `sentence-transformers/LaBSE`, `intfloat/multilingual-e5-base` | 05 | — | Taneesha |

The real-mode code is `backend/app/models/real/__init__.py`; switching is described in `docs/REAL_MODE.md`.

### 7.3 Classical models in the research experiments (CPU)

TF-IDF words + Naive Bayes, TF-IDF words (1–2) + logistic regression, TF-IDF characters (2–5) + logistic
regression, words + characters + logistic regression, and the rules + model hybrid (the model may only raise
urgency). All are trained in `backend/research/common.py` on `train.jsonl`; results are in `docs/research/`.

---

## 8. What is still to do

1. **Hand-written test set** (`data/queries/test.jsonl`, 300 per language) written by people who have not seen the
   app, using `docs/annotation/GUIDELINES.md`. Every report number should be confirmed on it.
2. **Verify every step** against the source PDFs (`docs/VERIFY.md`) and mark records `team_checked`.
3. **Train the transformers** (notebooks 03 → 04 → 01 → 02, then 05) and commit `transformers_results.json`.
4. **Native-speaker check** of all Hindi, Marathi and Hinglish text, which was machine-drafted.
5. Check the silver probe labels and write the 100-sentence negation sets per language.
