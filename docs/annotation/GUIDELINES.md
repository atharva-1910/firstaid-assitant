# Writing and labelling the hand-written test sets

The hand-written test set is the fair measure for the report (Section 10). Template data scores 1.00 for every method,
and the probe set has been used to fix the lexicons, so neither can show how the system does on real messages.

## 1. Query test set (`queries_{lang}.csv`, one per language owner)

**Target:** 50 messages per class per language: 300 per language, 1,200 in total. If time is short, 25 per class
(150 per language) still gives usable confidence intervals. Report the size you reach.

Classes: `unresponsive`, `heart_attack`, `choking`, `bites`, `burns`, `out_of_scope` (other emergencies such as a
fracture, stroke, fever, poisoning, seizure without unresponsiveness, and anything about a child or infant).

**Who writes:** people who have **not** used or seen the app's word lists: friends, family, classmates. Give them
a situation card (below) and ask: "You are next to this person. Type to an app what you see, the way you would
type it on your phone." The language owner collects and labels. Put the writer's initials in `written_by`.

Situation cards (spread messages evenly across them; within bites and burns, across the subtypes):

| Class | Cards to give writers |
|---|---|
| unresponsive | collapsed and not breathing; collapsed and breathing; fainted; not waking up; gasping |
| heart_attack | chest pain; chest pressure with sweating; pain spreading to arm or jaw; "heart attack" |
| choking | choking on food and cannot breathe; coughing hard after swallowing something; turning blue |
| bites | snake; bee or wasp, with and without face swelling; scorpion; dog or other animal |
| burns | hot liquid or steam; fire or stove, small and large; acid or chemical, skin and eyes; electric shock |
| out_of_scope | fracture, stroke, fever, poisoning, seizure, nosebleed; a child or baby in any of the above |

**Rules:**
- Write naturally: short, misspelt, mixed language, no punctuation are all fine. Do not tidy messages up.
- Hinglish is typed in the writer's own romanised spelling, never transliterated from Hindi.
- Never copy a message from `train.jsonl`, `dev.jsonl`, the safety suite or the probe set.
- Never use the test set to change lexicons, rules, prompts or thresholds. If you find a gap, note it in `notes`
  and fix it only after the final numbers are recorded, then report both.

**Labels** (follow the specification, Section 8.2):

| Column | Values | How to decide |
|---|---|---|
| `situation` | the six classes | what the writer was describing (the card) |
| `subtype` | unresponsive: `path_a` (not breathing / gasping) or `path_b` (breathing); bites: `snake`, `insect_sting`, `scorpion`, `dog`; burns: `fire_heat`, `chemical_acid`, `electrical`; otherwise empty | empty if the message does not say |
| `urgency` | `emergency`, `clinic`, `home`, or empty | apply Section 8.2: unresponsive, not breathing, chest pain, choking with weak or no cough, any snakebite, sting with allergy signs, electrical injury, chemical burn to eyes/face, burn larger than a palm or on face/neck/hands/feet/joints, any child: emergency. Dog bite and scorpion: clinic. Small burn, sting without allergy signs, choking with strong cough: home. **Empty** when the message does not give enough to decide (the app should ask a question). |

Import a finished sheet: `python -m research.annotation import docs/annotation/queries_hi.csv`. It checks every row and
refuses the file if any label is invalid.

## 2. Agreement (Cohen's kappa)

Pick 60 messages per language (10 per class). A second team member labels them **without seeing** the first labels,
in a copy of the sheet with the same `id`s. Then:

```bash
python -m research.annotation kappa docs/annotation/queries_hi.csv docs/annotation/queries_hi_second.csv
```

Report kappa for situation and urgency per language (above 0.8 is strong agreement, 0.6–0.8 substantial). Discuss each
disagreement, settle the final label, and say in the report how many changed. Urgency disagreements usually show
where the specification is unclear, which is itself a finding.

## 3. Negation test set (`negation_{lang}.csv`, owner of F3 with each language owner)

**Target:** 100 sentences per language (Section 8.5). One row per fact; a sentence that states two facts gets two rows
with the same `id`.

| Column | Values |
|---|---|
| `slot` | `responsive`, `breathing`, `chest_pain`, `power_off`, `allergy_signs` |
| `gold` | responsive / chest_pain / power_off / allergy_signs: `yes`, `no`, `uncertain`; breathing: `normal`, `abnormal`, `absent`, `uncertain` |

Cover, in roughly equal parts: plain affirmed; plain negated; uncertain ("shayad", "पता नहीं", "कदाचित", "I think");
negation far from its word ("seene mein koi dard ya pressure nahi"); two facts with "but/lekin/पण"; two facts with
"and/aur/आणि"; double negation ("aisa nahi ki saans nahi le rahe"); negation of a different fact than the symptom
("hosh mein hai lekin saans nahi"). Import with `python -m research.annotation negation docs/annotation/negation_mr.csv`,
then run `python -m research.e6_negation`; the owners' set becomes the headline row.

## 4. Checking the silver probe labels

`backend/data/queries/probe_labelled.jsonl` was labelled by Claude, following Section 8.2. One person checks all 100
rows (about 15 minutes), corrects any label, and changes `labelled_by` to their name.
