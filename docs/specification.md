# Multilingual First Aid Assistant: Complete Handover and Build Specification

Version 2.0 · October 2026 · CCNLP Mini Project, MIT-WPU

This file is a complete specification. Give it to an AI coding tool (or a developer) together with the instruction "Build this platform exactly as specified." Every section is binding unless marked optional.

> **Medical accuracy notice.** The first aid steps in Section 9 follow the sources listed in Section 4. Recommendations quoted from the AHA 2025 Adult Basic Life Support guideline and the AHA/Red Cross 2024 highlights were checked online. Every item marked **[VERIFY]** must still be checked against the source PDF by the situation owner, with the exact page filled in, before any demo. The app is a research demo, not medical advice.

---

## 0. Instructions for the AI tool building this

1. Build a working web app with a React frontend and a Python FastAPI backend, exactly as described in Sections 11 to 16.
2. **Never invent medical content.** All first aid text shown to users must be loaded from the content files in `backend/content/`. Do not generate, paraphrase or "improve" steps, warnings or questions.
3. Build in **stub mode first** (`MODEL_MODE=stub`): every NLP model has a simple rule-based stand-in so the whole app runs end to end with no GPU and no downloads. Real models plug in later behind the same interfaces (Section 12).
4. Follow the design system in Section 14 exactly: colours, font sizes, one step per screen, and red used only for emergency actions.
5. Do not call any external API at runtime. Everything runs locally.
6. Where content in Hindi, Hinglish or Marathi is missing, show the English text with a small "Translation pending" label. Never machine-translate inside the app.
7. Write the tests in Section 17. The safety test suite must pass before anything else is considered done.

---

## 1. Project summary

| Item | Value |
|---|---|
| Title | Multilingual First Aid Assistant: a source-cited procedure corpus and safety-first NLP models for English, Hindi, Hinglish and Marathi |
| Users | Untrained bystanders helping an adult before professional help arrives |
| Input | A typed description of the emergency in English, Hindi, Hinglish (romanised Hindi mixed with English) or Marathi |
| Output | An emergency alert when needed, then calm, one-at-a-time first aid steps with warnings and source citations, then a handover summary for the ambulance crew |
| Situations covered | Five, for adults: (1) unresponsive or unconscious, from any cause; (2) heart attack; (3) choking; (4) bites: snake, insect, dog; (5) burns: fire and heat, chemical and acid, electrical |
| Emergency number | 112 (India's single emergency number) |

---

## 2. Problem statement

When someone collapses, has chest pain, chokes, is bitten or is burned, the people nearby are the only help until an ambulance arrives. Most are untrained. They describe what they see in everyday words, in their own language, often in panic, and they often follow harmful home remedies, such as cutting and sucking a snakebite, putting chilli on a dog bite, or putting toothpaste on a burn.

Existing resources do not serve them well:

- Public first aid datasets are English-only lists of questions and answers. FirstAidQA (2025) has 5,550 synthetic pairs generated from a 2019 book; First-Aid-Dataset has fewer than 1,000 pairs. Neither stores step order, warnings or sources.
- Static first aid apps typically expect the user to already know the name of the condition and to browse menus, usually in English.
- General-purpose chatbots can sound confident while being wrong, do not cite the guideline behind each step, and are not evaluated for first aid safety in Indian languages or Hinglish.

**Research problem:** no first aid resource is at the same time structured, source-cited, multilingual (including code-mixed Hinglish) and tested for safety.

---

## 3. Our approach in one paragraph

We turn current, official first aid guidelines, all published after 2020, into a small, carefully checked corpus of five procedures. Each procedure is stored as structured data: recognition signs, branching steps, do-not rules, escalation triggers, and a page citation for every step. On top of it, an NLP pipeline understands a free-text description in English, Hindi, Hinglish or Marathi, extracts the key facts, decides how urgent the situation is, identifies the situation and its subtype, asks one well-chosen question if unsure, and then shows the verified steps one at a time in the user's language. Safety-critical decisions always have a rule-based floor, so a model can make the system more cautious but never less.

---

## 4. Data sources (all published after 2020)

### 4.1 First aid guidelines

| # | Source | Published | Publisher | Role | Link |
|---|---|---|---|---|---|
| G1 | International First Aid, Resuscitation and Education Guidelines 2025 | March 2026 | IFRC (International Federation of Red Cross and Red Crescent Societies) | Main source for all five situations | https://www.ifrc.org/media/78476 |
| G2 | 2024 American Heart Association and American Red Cross Guidelines for First Aid (Circulation, DOI 10.1161/CIR.0000000000001281) | November 2024 | AHA and American Red Cross | Heart attack (chest pain), burns (thermal and chemical), snakebite, bee and wasp stings | https://www.ahajournals.org/doi/10.1161/CIR.0000000000001281 |
| G3 | 2025 AHA Guidelines for CPR and Emergency Cardiovascular Care, Part 7: Adult Basic Life Support | October 2025 | AHA | Unresponsive (CPR) and choking | https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/adult-basic-life-support |
| G4 | 2025 International Consensus on First Aid Science With Treatment Recommendations | 2025 | ILCOR (International Liaison Committee on Resuscitation) | Evidence strength (recovery position, aspirin for chest pain, burn cooling and others) | https://www.ilcor.org/uploads/FA-2025-COSTR-Full-Chapter.pdf |
| G5 | National Action Plan for Prevention and Control of Snakebite Envenoming (NAPSE) | Launched 2024 | Ministry of Health and Family Welfare, Government of India | Indian context: harmful snakebite practices | https://ncdc.mohfw.gov.in/wp-content/uploads/2024/07/NATIONAL-ACTION-PLAN-FOR-PREVENTION-AND-CONTROL-OF-SNAKEBITE-ENVENOMING-NAPSE.pdf |

**Where each situation is covered** (G1 page numbers are the section start pages from its table of contents):

| Situation | G1 IFRC 2025 | G2 AHA/Red Cross 2024 | G3 AHA 2025 BLS | G4 ILCOR 2025 | G5 NAPSE |
|---|---|---|---|---|---|
| Unresponsive or unconscious | Unresponsive and breathing normally, p. 152; unresponsive and abnormal breathing (adult), p. 158; with a defibrillator, p. 196 | Positioning of the ill or injured person | Recognition, CPR, compression-only CPR, AED | Recovery position | — |
| Heart attack | Chest pain (cardiac), p. 358 | Chest pain | — | Aspirin for chest pain | — |
| Choking | Choking, p. 238 | — | Foreign-body airway obstruction | — | — |
| Bites | Mammal bites, p. 323; insect bites or stings, p. 326; snakebites, p. 340 | Snakebite; bee and wasp stings; spider and scorpion envenomation | — | — | Harmful practices (p. 2) |
| Burns | Burns, p. 288 | Cooling of thermal burns; care after cooling; chemical exposures to skin and eye | — | Burn cooling | — |

**Known gap:** electrical injury is not a separate topic in G1's table of contents or in G2's topic list. The burns owner must check whether G1's Burns section (p. 288) covers electrical burns. Until a post-2020 source is confirmed, the electrical branch shows only scene safety, "Call 112", CPR if needed and cooling of visible burns, all of which G1 and G3 support in general terms.

The older files `FA-manual-1.pdf` (Indian First Aid Manual, 2016) and `PIIS0300957225002643.pdf` (ERC 2025) in the project folder are **not used**.

### 4.2 Datasets the team builds

| Dataset | Contents | Size | Format |
|---|---|---|---|
| Procedure corpus | The five situations with their subtypes, written in the team's own words with page citations | 5 records | JSON, one file per situation |
| Query set | Everyday descriptions of emergencies, labelled with situation, subtype, urgency and key facts | 4,800 queries (Section 10) | JSON Lines |
| Myth set | Harmful home remedies and wrong actions, each with the reason it is harmful | About 40 per language | JSON Lines |
| Safety test suite | Must-pass queries where missing an emergency is unacceptable | 50 per language | JSON Lines |

### 4.3 Supporting NLP resources (all published after 2020)

| Resource | Year | Used for |
|---|---|---|
| IndicLID (Bhasha-Abhijnaanam, AI4Bharat) | 2023 | Language identification, including romanised Hindi (Hinglish) |
| IndicXlit (Aksharantar, AI4Bharat) | 2022 | Converting Hinglish to Devanagari |
| IndicTrans2 (AI4Bharat) | 2023 | Translating English queries and content while building the dataset, followed by native-speaker checks |
| IndicXNLI (AI4Bharat) | 2022 | Training data for the entailment model in Hindi and Marathi |

---

## 5. How this differs from existing tools (novelty)

| Capability | Existing first aid datasets | Static first aid apps | General chatbots | **Our system** |
|---|---|---|---|---|
| Understands free text in Hindi, Marathi and Hinglish | No | Typically no | Partly | **Yes, evaluated per language** |
| Ordered, branching steps | No | Yes | Inconsistent | **Yes, stored as a step graph** |
| Page citation for every step | No | Rarely | No | **Yes** |
| Compares several guidelines and shows disagreement | No | No | No | **Yes** |
| Emergency alert shown before any steps | No | Sometimes | Inconsistent | **Yes, with a rule-based floor** |
| Detects harmful Indian home remedies | No | No | Inconsistent | **Yes** |
| Asks a clarifying question instead of guessing | No | No | Sometimes | **Yes, chosen by information gain** |
| Explains why it raised an alert | No | No | No | **Yes, highlighted trigger words** |
| Handover summary for the ambulance crew | No | No | No | **Yes, built only from what the user said** |

### The four unique selling points

1. **Procedure graphs, not flat Q&A:** branching steps with a page citation for each.
2. **Answers that cite and never guess:** steps come from verified records; when unsure, the system asks one well-chosen question.
3. **Multi-guideline comparison:** each step shows whether the guidelines agree, and how strong the evidence is.
4. **Safety parity across languages:** emergency alerts and harmful-remedy warnings tested to be equally reliable in English, Hindi, Hinglish and Marathi.

---

## 6. Scope

### 6.1 Ownership: one language, one feature, one model each; situations shared five ways

| Member | PRN | Language owned | NLP feature owned | Situation(s) owned | Model owned |
|---|---|---|---|---|---|
| Taneesha Badhe | 1032232190 | English | Symptom and detail extraction (F1) | Unresponsive or unconscious; heart attack | BGE-M3: situation identification |
| Atharva Hemade | 1032232249 | Hindi | Smart clarifying question and conversation memory (F2) | Choking | Gemma 3: optional step rephrasing |
| Siddhi Karhekar | 1032232132 | Marathi | Negation and uncertainty handling (F3) | Bites: snake, insect, dog | mmBERT: step verification and guideline comparison |
| Soham Ghodake | 1032232337 | Hinglish | Explainable emergency alert (F4) | Burns: fire and heat, chemical and acid, electrical | IndicBERT v2: urgency triage and harmful-action detection |

Taneesha owns two situations because unresponsive and heart attack are closely linked: a heart attack can lead to the person becoming unresponsive.

Owning a **language** means: writing and checking the queries, myth set and safety suite in that language, and checking every translated step and UI string. Owning a **situation** means: writing its procedure record, checking every step against all listed sources, filling page numbers, and logging where the sources differ.

### 6.2 In scope

- Five situations with their subtypes, adults only, covered in full detail and checked against the sources.
- Typed input in English, Hindi, Hinglish and Marathi.
- Detection of urgency (emergency, clinic, home), situation and subtype, out-of-scope situations, and child or infant cases.
- Four NLP features (F1 to F4) plus the safety rules layer.
- A mobile-first web app with the screens in Section 15.
- An evaluation per language, with safety measures reported first.

### 6.3 Out of scope

- Any other situation (for example stroke, seizures without unresponsiveness, fractures, severe bleeding not caused by a bite, poisoning). The app recognises these and shows the out-of-scope screen.
- Children and infants. The app recognises them, shows "Call 112", and explains that child guidance is not yet covered.
- Medical diagnosis or treatment advice; the app never names a cause of unconsciousness.
- Voice input and output, offline or on-phone models, images or video (possible future work).
- Placing calls: the app offers a "Call 112" link, and the user makes the call.

---

## 7. System architecture

### 7.1 Runtime workflow for one message

```
User message (English, Hindi, Hinglish or Marathi)
   │
   ▼
[1] Normalise ─ Unicode clean-up, Devanagari digits → 0-9, typo correction
   │
   ▼
[2] Language identification ─ IndicLID (native vs romanised); Hinglish → Devanagari with IndicXlit
   │
   ▼
[3] F1 Detail extraction ─ age group, responsiveness, breathing, chest pain, choking signs,
   │                         bite type, burn cause, burn area, power still on, time, actions taken
   │     └── F3 Negation and uncertainty applied to every extracted fact
   ▼
[4] Safety layer ─ rules floor + IndicBERT v2 triage + harmful-action check
   │     ├── emergency → "Call 112" screen first (with F4 explanation)
   │     └── harmful action mentioned → warning card first
   ▼
[5] Situation identification ─ BGE-M3 over the 5 records + out-of-scope class; subtype from F1 slots
   │     ├── child or infant → child screen
   │     ├── out of scope → out-of-scope screen
   │     └── low confidence, unknown subtype, or a critical fact unknown → F2 clarifying question
   ▼
[6] Steps ─ loaded from the verified record and branch, in the user's language
   │     └── optional Gemma 3 rephrasing, accepted only if mmBERT verifies it; otherwise the verified text
   ▼
[7] Step-by-step screens ─ one step at a time, warnings, source and agreement chips
   │
   ▼
[8] Handover summary ─ template filled from conversation memory (F2) and extracted facts (F1)
```

Conversation memory (F2) stores every extracted fact per session, so later messages update the picture instead of starting over. If a later message changes the situation (for example a heart attack patient becomes unresponsive), the app switches to the new situation and says so.

### 7.2 Offline workflow (building the data and models)

1. Download the guideline PDFs (Section 4.1) and extract text with page numbers (PyMuPDF).
2. Each situation owner writes the procedure record and fills every page number, agreement label and evidence label.
3. Run IndicTrans2 to translate steps and UI strings into Hindi and Marathi; the Hinglish owner writes Hinglish versions by hand. Each language owner checks every line.
4. Build the query set (Section 10), myth set and safety suite.
5. Train and evaluate baselines (TF-IDF with logistic regression, BM25), then the four models.
6. Run mmBERT across the guidelines to suggest agreement labels; the situation owner confirms each one by hand.
7. Switch the app from `MODEL_MODE=stub` to `MODEL_MODE=real`.

---

## 8. NLP components in detail

### 8.1 Models (all released after 2020)

| Model | Year | Role | Why this model | Stub-mode stand-in |
|---|---|---|---|---|
| IndicBERT v2 | 2023 | Urgency triage (emergency, clinic, home) and harmful-action detection | Trained on Indian languages; outputs a fixed label, so it cannot invent text | Keyword rules from the lexicons |
| BGE-M3 | 2024 | Identifies which of the 5 situations (or out of scope) a message describes | Places all languages in one shared meaning space | Keyword overlap score per situation |
| mmBERT | 2025 | Verifies that a rephrased step says the same as the verified step; suggests agreement labels between guidelines (offline) | Modern multilingual encoder suited to comparing two sentences | Always reject rephrasing; use verified text |
| Gemma 3 4B | 2025 | Optional: rephrases a step more simply, using only the current record | Fluent in Hindi and Marathi; open weights; runs locally through Ollama or on Colab when quantised | Disabled |

Hinglish is detected by IndicLID, converted to Devanagari by IndicXlit, and then handled by the same models as Hindi. It is evaluated separately. Baselines for the report: TF-IDF with logistic regression, BM25, and MuRIL (2021) as a Hinglish comparison.

### 8.2 Safety rules floor (always on, in both modes)

Rules run before and after the models. A model may raise urgency but can never lower it below the rules.

| Condition (after negation handling) | Forced result |
|---|---|
| Unresponsive, or breathing absent, abnormal or only gasping | Emergency; situation = unresponsive |
| Chest pain or pressure, or a stated "heart attack" | Emergency; situation = heart attack |
| Choking with weak cough, no sound, or cannot breathe | Emergency |
| Any person who becomes unresponsive during another situation | Emergency; switch to unresponsive |
| Any snakebite, or a bite from an unknown animal that might be a snake | Emergency |
| Sting or bite followed by trouble breathing, swelling of face, lips or throat, widespread rash, or faintness | Emergency (possible severe allergic reaction) |
| Scorpion sting | Clinic or hospital at minimum [VERIFY] |
| Dog bite | Clinic the same day at minimum (rabies risk); emergency if bleeding will not stop or bites are deep or on the face [VERIFY] |
| Any electrical injury | Emergency |
| Chemical or acid burn to the eyes or face, a large area, or an acid attack | Emergency [VERIFY] |
| Thermal burn larger than the person's palm, on face, neck, hands, feet, genitals or joints, or with breathing difficulty | Emergency [VERIFY thresholds] |
| Child or infant mentioned | Emergency; child screen |
| Breathing, responsiveness or "is the power off" is uncertain | Ask the F2 question about it before showing steps, with "Call 112" visible |

### 8.3 Feature F1: symptom and detail extraction (owner: Taneesha)

**What it does:** pulls structured facts out of free text.

| Slot | Values |
|---|---|
| `age_group` | adult, child, infant, unknown (from words and numbers, e.g. "60 saal", "६० वर्षांचे") |
| `responsive` | yes, no, unknown |
| `breathing` | normal, abnormal, absent, unknown |
| `chest_pain` | yes, no, unknown |
| `choking_signs` | coughing_strongly, weak_or_silent, none, unknown |
| `bite_type` | snake, insect_sting, scorpion, dog, other_mammal, unknown |
| `allergy_signs` | yes, no, unknown |
| `burn_cause` | fire_heat, hot_liquid_steam, chemical_acid, electrical, unknown |
| `burn_area` | small, large, eyes_or_face, sensitive_area, unknown |
| `power_off` | yes, no, unknown (electrical only) |
| `time_since` | free text, e.g. "10 minutes" |
| `actions_taken` | list of actions the user says they already did |

**How to build:** spaCy with an `EntityRuler` per language, fed by pattern lists in `content/lexicons/{lang}.json`. Normalise Devanagari digits (०–९) to 0–9 before matching numbers. Use rapidfuzz (score ≥ 85) for typo-tolerant matching. Hinglish lexicons include common spellings ("saans", "sans", "saas"; "behosh", "behos").

**Done when:** slot F1 ≥ 0.85 on the human-written English test set, and the safety suite passes.

### 8.4 Feature F2: smart clarifying question and conversation memory (owner: Atharva)

**Clarifying question:** asked when the top situation's confidence is below 0.75, when the top two are within 0.15 of each other, when the subtype is unknown (bite type, burn cause), or when a safety slot (`responsive`, `breathing`, `power_off`) is unknown.

**How the question is chosen (information gain):**

1. Take the candidate situations and subtypes and their probabilities.
2. Each question in `content/questions.json` lists the answer expected for each candidate.
3. For each question, compute the expected reduction in uncertainty (entropy) over the candidates.
4. Ask the question with the highest gain. Safety questions always win when their slots are unknown.
5. Ask at most 2 questions in a row; if still unsure, show "Call 112" and the most likely situation.

**Question bank (English source; translations by language owners):**

| id | Question | Options |
|---|---|---|
| q_responsive | Does the person respond when you tap their shoulders and speak loudly? | Yes · No · Not sure |
| q_breathing | Is the person breathing normally? | Yes · No, or only gasping · Not sure |
| q_chest_pain | Do they have pain, pressure or tightness in the chest? | Yes · No |
| q_can_cough | Can the person cough, speak or breathe? | Yes, coughing strongly · No, or very weakly |
| q_bite_type | What bit or stung them? | Snake · Insect or bee · Scorpion · Dog or other animal · Not sure |
| q_allergy | Is there swelling of the face or throat, trouble breathing, or a rash spreading over the body? | Yes · No |
| q_burn_cause | What caused the burn? | Fire or hot object · Hot liquid or steam · Chemical or acid · Electricity |
| q_power_off | Is the electricity switched off, or is the person clear of the source? | Yes · No · Not sure |
| q_age | Is the person an adult, a child or a baby? | Adult · Child · Baby |

**Conversation memory:** an in-memory store keyed by `session_id` (expires after 2 hours). Each message updates the slots; a newer, certain value replaces an older or uncertain one. The current slots are returned with every response.

**Done when:** on ambiguous test queries, the right situation and subtype are reached within 2 questions in at least 90% of cases.

### 8.5 Feature F3: negation and uncertainty handling (owner: Siddhi)

**What it does:** decides whether each extracted fact is affirmed, negated or uncertain. "Not breathing" must set `breathing = absent`, not `normal`.

| Language | Negation cues | Uncertainty cues | Where the cue usually sits |
|---|---|---|---|
| English | not, no, isn't, can't, cannot, unable, without, never | maybe, might, I think, not sure, probably | Before the word it negates |
| Hindi | नहीं, न, मत, बिना | शायद, लगता है, पता नहीं | Before the verb |
| Hinglish | nahi, nahin, nhi, na, mat, bina | shayad, lagta hai, pata nahi | Before the verb |
| Marathi | नाही, नको, न, विना | कदाचित, वाटतं, माहीत नाही | After the verb |

**How to build:** for English use negspacy. For the other languages, apply each cue to the nearest symptom term within 3 tokens, searching first in the direction given in the table. An uncertain fact on a safety slot triggers the F2 question for that slot. Language owners extend the cue lists.

**Done when:** negation accuracy ≥ 0.90 on a 100-sentence test set per language, and zero safety-suite failures caused by negation.

### 8.6 Feature F4: explainable emergency alert (owner: Soham)

**What it does:** shows which of the user's own words triggered the alert, under a "Why this alert?" link, e.g. "Because you said: **saans nahi le rahe**".

**How to build:** in real mode, token attributions from transformers-interpret (or SHAP) on the IndicBERT v2 triage model; show the top 1 to 3 words above a threshold, merged back to whole words and mapped back to the user's original Hinglish spelling. In stub mode, show the words that matched the safety rules. Rule-triggered alerts always name the rule's trigger words.

**Done when:** in a manual check of 50 emergency queries per language, the highlighted words are judged relevant in at least 90% of cases.

---

## 9. The five situations (content)

All five cover **adults only**. Each step carries its source. Steps marked **[VERIFY]** must be checked by the situation owner against every listed source, with the exact page filled in and any disagreement recorded. Text marked **(checked)** matches a recommendation read in the source during preparation of this spec.

### 9.1 Unresponsive or unconscious, from any cause · owner: Taneesha

**Recognition:** does not respond to a loud voice or a tap on the shoulders. The app never guesses the cause.

**Urgency:** always emergency.

**Branching:** after step 3, the path splits on `breathing`.

| # | Step | Source |
|---|---|---|
| 1 | Make sure the area is safe for you. If electricity may be involved, do not touch them until the power is off. | G1 p. 152 [VERIFY] |
| 2 | Tap their shoulders and ask loudly, "Are you all right?" | G1 p. 152 [VERIFY] |
| 3 | Look at the chest for up to 10 seconds. Are they breathing normally? | G1 p. 158 [VERIFY] |
| **Path A: not breathing, or only gasping** | | |
| A1 | Call 112 now and put the phone on speaker. | G3: call first, then start CPR; hands-free phone (checked) |
| A2 | Ask someone to bring an AED (defibrillator) if one is nearby. | G1 p. 196 [VERIFY] |
| A3 | Put the heel of one hand in the centre of the chest, the other hand on top, arms straight. | G1 p. 158 [VERIFY] |
| A4 | Push hard and fast: at least 5 cm deep but not more than 6 cm, 100 to 120 times a minute. Let the chest rise fully each time. | G3 (checked) |
| A5 | If you are trained and willing, give 2 breaths after every 30 pushes. If not, keep pushing without stopping. | G3: compression-only is appropriate for untrained rescuers (checked); 30:2 ratio [VERIFY] |
| A6 | When the AED arrives, switch it on and follow its voice instructions. | G1 p. 196, G3 (checked) |
| A7 | Keep going until help takes over, they start breathing normally, or you cannot continue. | G1 p. 158 [VERIFY] |
| **Path B: breathing normally** | | |
| B1 | Call 112. | G1 p. 152 [VERIFY] |
| B2 | Roll them onto their side (recovery position) so their airway stays open, unless you think they have a neck or back injury. | G1 p. 152; G4 recovery position [VERIFY injury exception] |
| B3 | Keep checking their breathing. If it stops or becomes gasping, go to Path A. | G1 p. 152 [VERIFY] |
| B4 | Stay with them until help arrives. | G1 p. 152 [VERIFY] |

**Do not:** do not mistake occasional gasps for normal breathing (G3, checked); do not give food, water or medicine by mouth; do not throw water on the face or make them sit up; do not make them smell onions or shoes; do not leave them alone. [VERIFY]

**UI extra:** on steps A3 to A7, show a calm pulsing circle at 110 beats per minute to guide pushing speed (Section 14.6).

### 9.2 Heart attack · owner: Taneesha

**Recognition:** pain, pressure, squeezing or tightness in the chest, which may spread to the arm, jaw, neck or back; may come with breathlessness, sweating, nausea or feeling faint. Symptoms can be mild. [VERIFY]

**Urgency:** always emergency.

| # | Step | Source |
|---|---|---|
| 1 | Call 112 now. Do not wait to see if the pain passes. | G1 p. 358 [VERIFY] |
| 2 | Help them sit in the position they find most comfortable, and keep them still and calm. | G1 p. 358 [VERIFY] |
| 3 | Loosen tight clothing. | G1 p. 358 [VERIFY] |
| 4 | If they are not allergic to aspirin and have not been told not to take it, give aspirin to chew. | G1 p. 358; G2 chest pain; G4 aspirin for chest pain [VERIFY dose: record each source's dose; the app shows the dose only after it is confirmed] |
| 5 | If they have their own prescribed medicine for chest pain, help them take it. | G1 p. 358 [VERIFY] |
| 6 | Ask someone to find an AED if one is nearby. | G1 p. 358 [VERIFY] |
| 7 | Stay with them. If they become unresponsive and are not breathing normally, start CPR (Situation 9.1, Path A). | G3 (checked) |

**Do not:** do not let them walk around or exert themselves; do not give food or drink; do not treat it as gas or acidity and wait; do not give aspirin if they are allergic to it. [VERIFY]

### 9.3 Choking · owner: Atharva

**Recognition:** suddenly cannot speak, breathe or cough, often while eating; may clutch the throat.

**Urgency:** emergency if the cough is weak or silent or they cannot breathe; otherwise watch closely.

| # | Step | Source |
|---|---|---|
| 1 | Ask, "Are you choking?" If they can cough strongly, let them keep coughing and watch them closely. | G3: allow coughing, observe for signs of severe obstruction (checked) |
| 2 | If the cough is weak or they cannot breathe or speak, call 112, or ask someone to call. | G3: activate emergency response for severe obstruction (checked) |
| 3 | Stand slightly behind them, support their chest with one hand and lean them forward. | G1 p. 238 [VERIFY] |
| 4 | Give 5 firm back blows between the shoulder blades with the heel of your hand. | G3: 5 back blows (checked); technique G1 p. 238 [VERIFY] |
| 5 | Then give 5 abdominal thrusts: stand behind them, place a fist just above the belly button, hold it with your other hand, and pull sharply inwards and upwards. | G3: followed by 5 abdominal thrusts (checked); technique G1 p. 238 [VERIFY] |
| 6 | Keep repeating 5 back blows and 5 abdominal thrusts until the object comes out or they become unresponsive. | G3 (checked) |
| 7 | If they become unresponsive, start CPR, beginning with chest pushes (Situation 9.1, Path A). | G3 (checked) |
| 8 | After abdominal thrusts, they should see a doctor, even if they feel fine. | G1 p. 238 [VERIFY] |

**Do not:** do not sweep inside the mouth with your finger unless you can clearly see the object; do not give water or food; do not hit their back while they are still coughing strongly. [VERIFY]

**Out of scope note:** for pregnant people or people too large to reach around, the app shows "Call 112" and notes that this case is not covered. [VERIFY whether G1 recommends chest thrusts]

### 9.4 Bites · owner: Siddhi

The subtype comes from `bite_type`; if unknown, ask `q_bite_type`.

#### 9.4a Snakebite

**Urgency:** always emergency. G2: "Emergency services should be activated for any person bitten by a venomous or possibly venomous snake" (checked).

| # | Step | Source |
|---|---|---|
| 1 | Call 112 or get them to the nearest hospital immediately. | G2 (checked); G1 p. 340 [VERIFY] |
| 2 | Move away from the snake. Do not try to catch or kill it. | G1 p. 340 [VERIFY] |
| 3 | Keep the person calm and as still as possible. | G1 p. 340 [VERIFY] |
| 4 | Keep the bitten arm or leg still, as you would a broken limb. | G1 p. 340 [VERIFY] |
| 5 | Remove rings, bangles, watches and tight clothing near the bite before swelling starts. | G1 p. 340 [VERIFY] |
| 6 | Note the time of the bite. | G1 p. 340 [VERIFY] |

**Do not:** do not tie a tourniquet; do not cut or suck the wound; do not use herbal remedies (G5 names all three as harmful, p. 2, checked); do not apply ice; do not wait for symptoms before going to hospital. [VERIFY ice]

**Known source difference to check:** whether a pressure bandage is recommended differs between guidelines and regions; record each source's position. [VERIFY]

#### 9.4b Insect bites and stings (bee, wasp, ant) and scorpion stings

**Urgency:** emergency if any allergy signs (`q_allergy`) or many stings; scorpion sting → clinic or hospital at minimum [VERIFY]; otherwise home care.

| # | Step | Source |
|---|---|---|
| 1 | Watch for a severe allergic reaction: trouble breathing, swelling of the face, lips or throat, a spreading rash, or feeling faint. If any appear, call 112. | G2: activate emergency services for anaphylaxis after a bee, wasp or hornet sting (checked); G1 p. 326 [VERIFY] |
| 2 | If a sting is left in the skin, remove it quickly. | G1 p. 326 [VERIFY method] |
| 3 | Wash the area with soap and water. | G1 p. 326 [VERIFY] |
| 4 | Apply a cold pack wrapped in cloth to ease pain and swelling. | G1 p. 326 [VERIFY] |
| 5 | For a scorpion sting, take them to a clinic or hospital. | G2 spider and scorpion envenomation [VERIFY] |

**Do not:** do not squeeze or scratch the area; do not apply mud, lime or other home remedies. [VERIFY]

#### 9.4c Dog bite (and other mammal bites)

**Urgency:** clinic the same day at minimum, because of rabies risk; emergency if bleeding will not stop, the bites are deep or many, or on the face or neck. [VERIFY]

| # | Step | Source |
|---|---|---|
| 1 | Move away from the animal to a safe place. | G1 p. 323 [VERIFY] |
| 2 | Wash the wound right away with plenty of running water and soap for about 15 minutes. | G1 p. 323 [VERIFY duration] |
| 3 | If it is bleeding, press on it with a clean cloth. | G1 p. 323 [VERIFY] |
| 4 | Cover it with a clean dressing. | G1 p. 323 [VERIFY] |
| 5 | Go to a clinic or hospital today, even for a small bite or scratch, to ask about rabies vaccination. | G1 p. 323 [VERIFY] |

**Do not:** do not put chilli powder, turmeric, oil, lime or other home remedies on the wound; do not ignore a small bite or scratch. [VERIFY]

### 9.5 Burns · owner: Soham

The subtype comes from `burn_cause`; if unknown, ask `q_burn_cause`.

#### 9.5a Fire, hot objects, hot liquid or steam

**Urgency:** emergency if large (bigger than the person's palm), on face, neck, hands, feet, genitals or joints, or with breathing difficulty; clinic if blistered; home care for small, red, unbroken skin. [VERIFY thresholds]

| # | Step | Source |
|---|---|---|
| 1 | Stop the burning: move away from the heat; if clothes are on fire, stop, drop and roll. | G1 p. 288 [VERIFY] |
| 2 | Cool the burn under clean, cool running water as soon as possible, for at least 20 minutes. | G1 p. 288; G2 cooling of thermal burns; G4 burn cooling [VERIFY duration in each source] |
| 3 | Remove jewellery, belts and other tight items from the burned area. | G2: "promptly remove all jewelry, belts, and other tight items from burned areas" (checked) |
| 4 | Do not remove clothing that is stuck to the burn. | G1 p. 288 [VERIFY] |
| 5 | Cover the burn loosely with cling film or a clean cloth that does not leave fibres. | G1 p. 288; G2 care after cooling [VERIFY] |
| 6 | Keep the person warm: cool the burn, not the whole person. | G1 p. 288 [VERIFY] |
| 7 | Call 112 or go to a clinic based on the urgency shown on screen. | G1 p. 288 [VERIFY] |

**Do not:** do not use ice or ice water; do not apply butter, oil, ghee, toothpaste or other home remedies; do not burst blisters. [VERIFY]

#### 9.5b Chemical or acid burns

**Urgency:** emergency for eyes, face, a large area, or an acid attack. [VERIFY]

| # | Step | Source |
|---|---|---|
| 1 | Protect yourself: avoid touching the chemical; use gloves or a plastic bag if you can. | G1 p. 288 [VERIFY] |
| 2 | Call 112. | G1 p. 288 [VERIFY] |
| 3 | Brush off any dry powder, then remove clothing and jewellery that the chemical touched. | G2 chemical exposures to the skin [VERIFY] |
| 4 | Rinse the skin with large amounts of running water for at least 20 minutes. | G2 chemical exposures to the skin [VERIFY duration] |
| 5 | If it is in the eye, rinse the eye with running water, holding the eyelids open, and keep rinsing until help arrives. | G2 chemical exposures to the eye [VERIFY duration] |
| 6 | Cover the area loosely with a clean cloth. | G1 p. 288 [VERIFY] |

**Do not:** do not try to neutralise the chemical with anything else (such as baking soda, vinegar or milk); do not rub the area or the eye. [VERIFY]

#### 9.5c Electrical burns and electric shock

**Urgency:** always emergency, even if the burn looks small. [VERIFY; see the source gap in Section 4.1]

| # | Step | Source |
|---|---|---|
| 1 | Do not touch the person until the power is switched off at the main switch or plug, or they are clear of the source. | G1 scene safety [VERIFY] |
| 2 | Stay well away from high-voltage lines; wait for the power company or emergency services. | [VERIFY: source needed] |
| 3 | Call 112. | [VERIFY: source needed] |
| 4 | If they are unresponsive and not breathing normally, start CPR (Situation 9.1, Path A). | G3 (checked) |
| 5 | Once it is safe, cool any visible burns under running water and cover them loosely. | G1 p. 288 [VERIFY] |

**Do not:** do not touch them with bare hands or anything wet or metal while the power may be on. [VERIFY]

### 9.6 Myth set seed (for harmful-action detection)

Each language owner expands this to about 40 items, with local variations and phrasing.

| Harmful action | Situation | Reason shown to the user |
|---|---|---|
| Tying a tight band (tourniquet) above a snakebite | Snakebite | Named as a harmful practice by the Health Ministry (G5). |
| Cutting or sucking a snakebite | Snakebite | Named as a harmful practice by the Health Ministry (G5). |
| Using herbal remedies or going to a faith healer instead of hospital for a snakebite | Snakebite | Delays the anti-venom treatment that saves lives (G5). |
| Putting chilli powder, turmeric or oil on a dog bite | Dog bite | Does not clean the wound; washing with soap and water does. [VERIFY] |
| Ignoring a small dog bite or scratch | Dog bite | Even small bites can transmit rabies. [VERIFY] |
| Putting toothpaste, butter, oil or ghee on a burn | Burns | It traps heat and raises the risk of infection. [VERIFY] |
| Putting ice on a burn | Burns | It can damage the skin further. [VERIFY] |
| Neutralising an acid burn with another substance | Chemical burn | It can cause more damage; rinse with water instead. [VERIFY] |
| Touching a person still in contact with electricity | Electrical | You can be electrocuted too. [VERIFY] |
| Giving water to an unresponsive person | Unresponsive | They cannot swallow safely. [VERIFY] |
| Making an unconscious person smell onions or shoes | Unresponsive | It does not help and wastes time. [VERIFY] |
| Treating chest pain as gas and waiting | Heart attack | Delay can cost a life; call 112. [VERIFY] |
| Giving water to a choking person | Choking | It can block the airway further. [VERIFY] |

---

## 10. Query dataset

### 10.1 Size

Classes: 5 situations plus out of scope = 6. Within each situation, queries are balanced across subtypes (for example snake, insect, scorpion and dog for bites).

| Set | Per language (English, Hindi, Hinglish, Marathi) | Total |
|---|---|---|
| Training and development: 150 per class × 6, from templates and paraphrases | 900 | 3,600 |
| Test: 50 per class × 6, written by hand by the language owner | 300 | 1,200 |
| **Total** | **1,200** | **4,800** |

Out-of-scope queries describe other emergencies (stroke, fractures, fever, poisoning, seizures without unresponsiveness and so on) and child or infant cases.

### 10.2 Query record format (JSON Lines)

```json
{"id": "hg-bite-0042", "lang": "hinglish", "text": "khet mein saap ne kaat liya pair pe, kya karu", "situation": "bites", "subtype": "snake", "urgency": "emergency", "slots": {"age_group": "adult", "bite_type": "snake"}, "split": "test", "written_by": "human"}
```

### 10.3 Rules

- Gold labels come from the templates and the language owner, never from a paraphrasing model.
- Hinglish queries are written by hand in natural romanised spelling, including common misspellings; they are not transliterated from Hindi.
- Test queries are never used in training or as prompt examples.
- Every query in the safety suite has `"must_be_emergency": true` or `false` and is run on every build.

---

## 11. Tech stack

| Layer | Choice |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, react-i18next, lucide-react icons |
| Fonts | Noto Sans (English and Hinglish), Noto Sans Devanagari (Hindi and Marathi), from Google Fonts |
| Backend | Python 3.11, FastAPI, Pydantic v2, Uvicorn |
| NLP (runtime) | spaCy, negspacy, rapidfuzz, IndicLID, ai4bharat-transliteration (IndicXlit), FlagEmbedding (BGE-M3), Hugging Face Transformers, PyTorch, transformers-interpret |
| Optional generation | Gemma 3 4B through Ollama (local) or Transformers with bitsandbytes (Colab) |
| NLP (offline) | PyMuPDF, IndicTrans2, scikit-learn, rank-bm25, Hugging Face Datasets, PEFT |
| Storage | JSON and JSON Lines files; session memory in process |
| Training | Google Colab (GPU) notebooks, one per member |
| Testing | pytest (backend), Vitest (frontend), optional Playwright |
| Version control | GitHub |

---

## 12. Model modes and interfaces

The backend reads `MODEL_MODE` from `.env` (`stub` or `real`). Each component has one interface and two implementations:

```python
class LanguageId:            # IndicLID / script ranges + Hinglish word list
    def detect(self, text: str) -> dict:   # {"lang": "en|hi|hinglish|mr", "script": "latin|devanagari"}

class Triage:                # IndicBERT v2 / rules
    def predict(self, text: str, lang: str, slots: dict) -> dict:  # {"urgency": "emergency|clinic|home", "scores": {...}, "harmful": {...} | None}

class SituationClassifier:   # BGE-M3 / keyword overlap
    def predict(self, text: str, lang: str) -> list[dict]:  # [{"situation": "bites", "p": 0.82}, ...] incl. "out_of_scope"

class StepVerifier:          # mmBERT / always-reject
    def entails(self, verified: str, candidate: str, lang: str) -> bool

class Rephraser:             # Gemma 3 / disabled
    def rephrase(self, step: str, lang: str, record: dict) -> str | None

class Explainer:             # transformers-interpret / rule trigger words
    def explain(self, text: str, lang: str, urgency: str) -> list[dict]  # [{"word": "...", "start": 0, "end": 5, "weight": 0.7}]
```

Stub `LanguageId`: Devanagari characters (U+0900–U+097F) → Hindi or Marathi, decided by Marathi marker words (आहे, नाही, झालं, काय, आणि); Latin script → Hinglish if it contains words from the Hinglish lexicon (hai, nahi, kya, saans, gaya), otherwise English.

The pipeline always shows the verified step text unless a rephrased version passes `StepVerifier.entails` in both directions.

---

## 13. Data formats and API

### 13.1 Situation record (`backend/content/situations/{id}.json`)

Situation ids: `unresponsive`, `heart_attack`, `choking`, `bites`, `burns`. Bites and burns hold their subtypes as named branches.

```json
{
  "id": "burns",
  "owner": "Soham Ghodake",
  "age_scope": "adult",
  "names": {"en": "Burns", "hi": "", "hinglish": "", "mr": ""},
  "recognition": [{"en": "Red, painful, blistered, white or charred skin after heat, chemicals or electricity", "hi": "", "hinglish": "", "mr": ""}],
  "branch_on": "burn_cause",
  "branches": {
    "fire_heat": {
      "urgency_rules": [{"if": {"burn_area": "large"}, "urgency": "emergency"}],
      "steps": [
        {
          "id": "burns_fire_s3",
          "order": 3,
          "text": {"en": "Remove jewellery, belts and other tight items from the burned area.", "hi": "", "hinglish": "", "mr": ""},
          "source": {"doc": "G2", "page": null, "quote_checked": true},
          "also_in": [{"doc": "G1", "page": 288}],
          "agreement": "unchecked",
          "evidence": "unchecked",
          "next": "burns_fire_s4",
          "verified": false
        }
      ],
      "do_not": [{"text": {"en": "Do not use ice or ice water.", "hi": "", "hinglish": "", "mr": ""}, "reason": {"en": "It can damage the skin further.", "hi": "", "hinglish": "", "mr": ""}}]
    },
    "chemical_acid": {"steps": [], "do_not": []},
    "electrical": {"steps": [], "do_not": []}
  },
  "source_differences": [{"topic": "cooling duration", "notes": ""}],
  "review_status": "draft"
}
```

Situations without subtypes (`unresponsive`, `heart_attack`, `choking`) use `branch_on: null` and a single `"default"` branch; `unresponsive` additionally branches on `breathing` (paths A and B).

Allowed values: `agreement` = agree, differ, single_source, unchecked; `evidence` = strong, weak, good_practice, unchecked; `review_status` = draft, team_checked, expert_verified. A JSON Schema in `backend/content/schema/situation.schema.json` must reject a record with any step missing `source.doc`.

### 13.2 API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/analyze` | Main call: takes a message, returns the next screen |
| POST | `/api/answer` | Answer to a clarifying question |
| GET | `/api/situations/{id}?lang=mr&branch=snake` | Full record for one situation, for browsing |
| POST | `/api/summary` | Handover summary for a session |
| GET | `/api/health` | Status, model mode and versions |

**`POST /api/analyze` request:**

```json
{"session_id": null, "text": "papa gir gaye, saans nahi le rahe", "ui_lang": "auto"}
```

**Response (same shape for `/api/answer`):**

```json
{
  "session_id": "6f1c…",
  "detected_lang": "hinglish",
  "display_lang": "hinglish",
  "next_screen": "emergency",
  "urgency": "emergency",
  "situation": {"id": "unresponsive", "branch": "path_a", "confidence": 0.91},
  "child_or_infant": false,
  "out_of_scope": false,
  "clarifying_question": null,
  "explanation": [{"word": "saans nahi", "weight": 0.83}],
  "harmful_action": null,
  "slots": {"age_group": "adult", "responsive": "no", "breathing": "absent"},
  "steps": [{"id": "unr_a1", "order": 1, "text": "…", "source": {"doc": "G3", "page": null}, "agreement": "agree", "evidence": "strong", "translation_pending": false}],
  "do_not": [{"text": "…", "reason": "…"}],
  "disclaimer": "…"
}
```

`next_screen` is one of: `question`, `emergency`, `steps`, `harmful_warning`, `child`, `out_of_scope`, `summary`.

---

## 14. Design system: calm, clear, accurate

### 14.1 Principles

1. **One thing at a time.** One instruction or one question per screen.
2. **Calm by default.** Soft blue-teal and off-white. Red appears only for "Call 112" and emergency banners, nowhere else.
3. **Big and readable.** Large text, large buttons, high contrast, generous spacing.
4. **Nothing moves unexpectedly.** No flashing, shaking or auto-advancing screens.
5. **Always a way out.** "Call 112" is visible on every screen.
6. **Plain words.** Short imperative sentences, no medical jargon, no blame.

### 14.2 Colour tokens

| Token | Hex | Use |
|---|---|---|
| `bg` | #F5F8FA | Page background |
| `surface` | #FFFFFF | Cards |
| `primary` | #2F6F8F | Buttons, progress, links |
| `primary-soft` | #E6F0F5 | Selected options, info panels |
| `text` | #1F2933 | Main text |
| `text-muted` | #52606D | Secondary text, citations |
| `success` | #2F855A | "Done" ticks, completed steps |
| `caution-text` | #8A5A00 | Text inside do-not boxes |
| `caution-bg` | #FFF8E6 | Do-not box background |
| `emergency` | #C53030 | "Call 112" button and emergency banner only |
| `emergency-soft` | #FDECEC | Emergency banner background |
| `border` | #D9E2EC | Card borders and dividers |

All text and background pairs must meet WCAG 2.1 AA contrast (4.5:1 for normal text). An optional dark theme uses a deep navy background (#14212B) with the same hues lightened to keep AA contrast.

### 14.3 Typography and sizing

| Element | Size | Weight |
|---|---|---|
| Step text | 24 px | 600 |
| Question text | 22 px | 600 |
| Body text | 18 px | 400 |
| Citations and small notes | 14 px | 400 |
| Line height | 1.5 (1.6 for Devanagari) | — |

### 14.4 Layout and controls

- Mobile first; content column at most 480 px wide, centred on larger screens.
- 8 px spacing grid; cards with 16 px padding and 12 px rounded corners.
- Primary buttons full width, at least 56 px tall; at most two buttons per screen (answer screens may show up to five stacked options).
- Header on every screen: small app name, language selector (English, हिंदी, Hinglish, मराठी), and a red "Call 112" pill that opens `tel:112`.
- Progress shown as "Step 2 of 6" plus a thin progress bar in `primary`.

### 14.5 Writing style for all UI text

- Sentences of 12 words or fewer where possible.
- Start steps with a verb: "Press", "Cool", "Call", "Wash".
- Reassure once, briefly: "Help is on the way. You are doing well."
- Never show model confidence numbers to the user.

### 14.6 Motion

- Screen changes fade over 150 ms; nothing else animates.
- CPR rhythm guide: a soft circle in `primary` that gently grows and shrinks at 110 beats per minute, with an optional quiet click. With `prefers-reduced-motion`, show "Push about 2 times per second" instead.

---

## 15. Screens

| # | Screen | Contents |
|---|---|---|
| 1 | **Home** | Heading "What happened?"; a large text box with placeholder "Tell us in your own words"; a Continue button; five large tiles as shortcuts (Unconscious, Heart attack, Choking, Bites, Burns) with simple line icons; footer line with sources and disclaimer |
| 2 | **Clarifying question** | One question in 22 px; full-width answer buttons; "Call 112" pill visible |
| 3 | **Emergency** | Banner in `emergency-soft` with "This is an emergency"; a large red "Call 112 now" button; under it "Why this alert?" (F4 highlight); a `primary` button "While you wait: show me what to do" |
| 4 | **Harmful-action warning** | Calm caution card: "Please do not do this", the action, the reason in one sentence, and a button to continue to the right steps |
| 5 | **Step** | Step number and progress; step text in 24 px; any do-not box for that step; a small chip row: source and page, "Sources agree" or "Sources differ" (tap for note), evidence label; Back and "Done, next" buttons; CPR rhythm guide on the CPR steps |
| 6 | **Handover summary** | Heading "Read this to the ambulance team"; 3 to 5 short lines built from slots, e.g. "Adult. Bitten by a snake on the leg about 20 minutes ago. Limb kept still. Conscious and breathing."; Copy and Share buttons |
| 7 | **Child or infant** | "Call 112 now" button; one sentence that guidance for children and babies is not covered yet |
| 8 | **Out of scope** | "This app covers five situations: unconscious, heart attack, choking, bites and burns. For anything else, call 112 or go to the nearest hospital." |
| 9 | **About and sources** | The guidelines with links, the team, and the research-demo disclaimer |

### 15.1 Core UI strings (native-speaker check required)

| Key | English | Hindi | Hinglish | Marathi |
|---|---|---|---|---|
| `call_112` | Call 112 | 112 पर कॉल करें | 112 par call karein | 112 वर कॉल करा |
| `what_happened` | What happened? | क्या हुआ? | Kya hua? | काय झालं? |
| `own_words` | Tell us in your own words | अपने शब्दों में बताइए | Apne shabdon mein batayein | तुमच्या शब्दांत सांगा |
| `next` | Done, next | हो गया, आगे | Ho gaya, aage | झालं, पुढे |
| `back` | Back | पीछे | Peeche | मागे |
| `yes` | Yes | हाँ | Haan | हो |
| `no` | No | नहीं | Nahi | नाही |
| `not_sure` | Not sure | पता नहीं | Pata nahi | माहीत नाही |
| `do_not` | Please do not do this | कृपया ऐसा न करें | Kripya aisa na karein | कृपया हे करू नका |
| `reassure` | Help is on the way. You are doing well. | मदद आ रही है। आप अच्छा कर रहे हैं। | Madad aa rahi hai. Aap achha kar rahe hain. | मदत येत आहे. तुम्ही छान करत आहात. |
| `handover` | Read this to the ambulance team | यह एम्बुलेंस टीम को पढ़कर सुनाएँ | Yeh ambulance team ko padh kar sunayein | हे रुग्णवाहिका टीमला वाचून दाखवा |
| `breathing_q` | Is the person breathing normally? | क्या व्यक्ति सामान्य रूप से साँस ले रहा है? | Kya vyakti normal saans le raha hai? | ती व्यक्ती नीट श्वास घेत आहे का? |

---

## 16. Repository structure

```
firstaid-assistant/
├── frontend/
│   ├── src/
│   │   ├── screens/            Home, Question, Emergency, HarmfulWarning, Step, Summary, Child, OutOfScope, About
│   │   ├── components/         Header, Call112Button, StepCard, DoNotBox, SourceChips, ProgressBar, CprRhythm, AnswerButtons
│   │   ├── i18n/               en.json, hi.json, hinglish.json, mr.json
│   │   ├── api/client.ts
│   │   └── theme/tokens.ts     colour and size tokens from Section 14
│   └── index.html
├── backend/
│   ├── app/
│   │   ├── main.py             FastAPI app and routes
│   │   ├── pipeline.py         orchestrates steps 1–8 of Section 7.1
│   │   ├── normalize.py        Unicode, digits, typos
│   │   ├── langid.py           IndicLID, Hinglish detection, IndicXlit
│   │   ├── extract.py          F1
│   │   ├── negation.py         F3
│   │   ├── clarify.py          F2 question selection
│   │   ├── memory.py           F2 session store
│   │   ├── safety_rules.py     Section 8.2
│   │   ├── explain.py          F4
│   │   ├── summary.py          handover template
│   │   └── models/             stub/ and real/ implementations of Section 12
│   ├── content/
│   │   ├── situations/         unresponsive.json, heart_attack.json, choking.json, bites.json, burns.json
│   │   ├── lexicons/           en.json, hi.json, hinglish.json, mr.json
│   │   ├── questions.json
│   │   ├── myths.jsonl
│   │   └── schema/situation.schema.json
│   ├── data/queries/           train.jsonl, dev.jsonl, test.jsonl
│   └── tests/                  safety_suite.jsonl, test_safety.py, test_negation.py, test_extract.py, test_api.py
├── training/                   Colab notebooks: 01_situation_bge_m3, 02_rephrase_gemma3, 03_verifier_mmbert, 04_triage_indicbert
├── docs/                       this specification, datasheet, evaluation report
└── .env.example                MODEL_MODE=stub, OLLAMA_URL=http://localhost:11434
```

---

## 17. Testing and evaluation

### 17.1 Automated tests (must pass on every build)

| Test | Requirement |
|---|---|
| Safety suite | 100% of `must_be_emergency: true` cases return `urgency = emergency`, in every language |
| Negation | "not breathing" in all four languages sets `breathing = absent` |
| Subtypes | Snake, insect, scorpion and dog bites, and fire, chemical and electrical burns each reach their own branch |
| Content | Every step in every branch has a source; schema validation passes |
| No invented text | Every step text returned by the API exists in the content files, or passed verification |
| API | All endpoints return the documented shape |
| Child and out of scope | Child and out-of-scope test queries reach the right screen |

### 17.2 Research evaluation (reported per language, with the gap against English)

| Component | Metrics (safety first) |
|---|---|
| Triage (IndicBERT v2) | Missed-emergency rate, then emergency recall, precision and macro-F1 |
| Harmful-action detection | Harmful actions wrongly accepted, then F1 |
| Situation identification (BGE-M3) | Accuracy, macro-F1, subtype accuracy, out-of-scope detection F1 |
| Step verification (mmBERT) | Accuracy and macro-F1 on agree, differ and unrelated pairs |
| Rephrasing (Gemma 3) | Share of rephrasings rejected by the verifier; critical-error rate on a manually reviewed sample of 50 per language |
| F1 extraction | Slot-level F1 |
| F2 clarifying question | Share of ambiguous queries resolved within 2 questions |
| F3 negation | Accuracy on 100 sentences per language |
| F4 explanation | Share of highlights judged relevant on 50 emergency queries per language |

Each model is compared with its baseline (TF-IDF with logistic regression, or BM25), runs are repeated 3 times, and hyperparameters are tuned on the development set only.

---

## 18. Build order

| Phase | Work | Output |
|---|---|---|
| 1 | Scaffold frontend and backend; load content files; stub models; safety rules | App runs end to end in English in stub mode |
| 2 | All 9 screens with the design system; i18n for four languages | Complete, calm UI |
| 3 | F1, F3 and the safety suite | Correct facts and no missed emergencies in stub mode |
| 4 | F2 question selection and memory; handover summary | Multi-turn conversations, subtype questions |
| 5 | Situation owners verify every step against the sources and fill page numbers | `review_status: team_checked` |
| 6 | Language owners translate and check content and UI strings | All four languages complete |
| 7 | Train real models in Colab; plug in behind the interfaces; F4 with real attributions | `MODEL_MODE=real` |
| 8 | Evaluation and report | Results tables per language |

---

## 19. Definition of done

- [ ] The app runs locally with one command each for frontend and backend.
- [ ] All five situations and their subtypes show correct, cited steps in all four languages.
- [ ] Hinglish input is detected and handled correctly.
- [ ] "Call 112" is visible on every screen; red is used nowhere else.
- [ ] The safety suite passes at 100% in every language.
- [ ] Child, infant and out-of-scope queries are handled safely.
- [ ] Every [VERIFY] tag in this file is resolved, every page number is filled, and the electrical-injury source gap is closed or the branch is reduced to the confirmed steps.
- [ ] Records are marked `team_checked`, and the disclaimer is shown on the home and about screens.
- [ ] The evaluation report includes every metric in Section 17.2, per language.

---

## 20. Team

| Name | PRN |
|---|---|
| Taneesha Badhe | 1032232190 |
| Atharva Hemade | 1032232249 |
| Siddhi Karhekar | 1032232132 |
| Soham Ghodake | 1032232337 |

*Research demo, not medical advice. Guidance is drawn from the IFRC International First Aid, Resuscitation and Education Guidelines 2025; the 2024 AHA and American Red Cross Guidelines for First Aid; the 2025 AHA Guidelines for CPR and ECC; the 2025 ILCOR International Consensus on First Aid Science; and India's National Action Plan for Prevention and Control of Snakebite Envenoming. In an emergency, call 112.*