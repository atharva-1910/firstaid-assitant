"""Builds report_spec.json for the CCA1 report: structure, the team's own draft text, figure list, tables
and per-section writing notes. Numbers come from docs/research/*.json. Run build_docx.js afterwards."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RES = ROOT.parent / "research"
FIG = ROOT / "figures"
L = ["en", "hi", "hinglish", "mr"]
LN = {"en": "English", "hi": "Hindi", "hinglish": "Hinglish", "mr": "Marathi"}


def j(n):
    return json.loads((RES / n).read_text(encoding="utf-8"))


e1, e2, e3, e4, e5, e6, e7, e8, x = (j(f"{n}.json") for n in ("e1_models", "e2_transfer", "e3_robustness", "e4_corpus", "e5_calibration", "e6_negation", "e7_verifier", "e8_faithfulness", "report_extra"))
probe = next(k for k in e1 if k.startswith("probe"))
safety = next(k for k in e1 if k.startswith("safety"))
OLD = "rules before probe fixes (33802b7)"
HYB = "hybrid: rules before fixes + model"
WC = "TF-IDF words + chars + LR"
hw = "safety suite + probe"
d6 = e6["diagnostic (machine-drafted)"]
CUR, PROP, ENG, CTX = "current (3 tokens, language direction)", "proposed: current + clause-wide uncertainty", "English rule (cue before word only)", "ConText-style (whole clause)"
v7 = e7["results"]
VJ = next(k for k in v7 if k.startswith("word overlap"))
VC = next(k for k in v7 if k.startswith("chrF ≥"))
VG = "chrF + number/negation guard"
f2 = lambda v: f"{v:.2f}"  # noqa: E731
pc = lambda v: f"{100 * v:.0f}%"  # noqa: E731

blocks = []
add = blocks.append
fignum = [0]
FIGREF = {}


def fig(fid, caption):
    fignum[0] += 1
    FIGREF[fid] = fignum[0]
    add({"type": "figure", "path": str(FIG / f"{fid}.png"), "caption": f"Figure {fignum[0]}. {caption}"})


def notes(title, items):
    add({"type": "notes", "title": title, "items": items})


def p(text, style="body"):
    add({"type": "p", "text": text, "style": style})


def h(text, level=1):
    add({"type": "h", "text": text, "level": level})


# ------------------------------------------------------------------ front matter
add({"type": "title", "text": "Multilingual First Aid Assistant"})
add({"type": "subtitle", "text": "CCA1 Report · CCNLP Mini Project · MIT World Peace University, Pune"})
add({"type": "table", "widths": [2000, 1500, 1200, 2300, 2360], "header": ["Name", "PRN", "Language", "Feature", "Model"], "rows": [
    ["Taneesha Badhe", "1032232190", "English", "F1 detail extraction", "BGE-M3 situation identification"],
    ["Atharva Hemade", "1032232249", "Hindi", "F2 clarifying question, memory", "Char n-gram language ID; Gemma 3 rephrasing"],
    ["Siddhi Karhekar", "1032232132", "Marathi", "F3 negation and uncertainty", "mmBERT step verification"],
    ["Soham Ghodake", "1032232337", "Hinglish", "F4 explainable alert", "IndicBERT v2 urgency triage"],
]})
p("Problem statement. Bystanders who help an injured adult before the ambulance arrives are usually untrained, describe the scene in their own language, and often follow harmful home remedies. Existing first aid datasets are English-only question–answer lists without step order or sources, and general chatbots do not cite guidelines or get tested for safety in Indian languages. There is no first aid resource that is structured, source-cited, multilingual (including code-mixed Hinglish) and tested for safety at the same time.", "draft")
notes("How to use this file", [
    "Black text is your first draft, kept as you wrote it. Yellow boxes list the facts and figure numbers each section should cover; write those paragraphs in your own words and then delete the boxes.",
    "Every figure is plotted by the code in backend/research/ from the project's data (python -m research.report, then python -m research.report_figures); corpus figures are screenshots of the real data files. No drawings or AI-generated images are included.",
    "The Model column above names transformer models that are not trained yet. Either run training/03, 04 and 05 on Colab before the evaluation and report those results, or mark them as planned (see the notes in 2.5).",
])

# ------------------------------------------------------------------ 1-2
h("1. Abstract")
p("We present a web assistant that helps an untrained bystander give first aid to an adult in five situations: unresponsiveness, heart attack, choking, bites and burns. Users describe the emergency in English, Hindi, Hinglish or Marathi, by typing or speaking. A pipeline normalises the text, identifies the language with a trained character n-gram model, extracts twelve safety-relevant facts with negation and uncertainty handling, and applies a rule-based safety floor that a model can raise but never lower. The system then raises an emergency alert with the user's own trigger words, asks at most two information-gain questions when unsure, and shows verified steps one at a time, each citing IFRC 2025, AHA 2024/2025 or the Indian NAPSE plan, with openly licensed illustrations on key steps. We built a 3,600-message query corpus (900 per language), a 103-case safety suite and a 100-message hand-written probe set. On template data every safety measure is perfect, but on the harder probe set emergency recall was only 0.77–0.92. The probe exposed missing phrasings such as \"saans ruk gayi\" and \"chest heavy\"; adding them raised probe recall to 1.00, although the probe set is then no longer unseen. The trained language identifier reaches 1.00 on the probe set against 0.97 for word lists, and a cross-language safety net cuts missed emergencies under a wrong language guess from 55 of 85 to none.", "draft")
notes("Update the abstract (keep it within 200 words; the draft is about 230)", [
    "The probe set was drafted by the build tool (written_by: claude in langid_probe.jsonl), not by people; describe it as a probe set of short, misspelt, code-mixed messages, not as hand-written.",
    f"Add the hybrid result: a TF-IDF model trained only on template data, placed under the rules floor, catches all {e1[probe][OLD]['all']['missed_emergencies']} probe emergencies the rules missed before the lexicon fix, at the cost of flagging {pc(e1[probe][HYB]['all']['false_alarm_rate'][0])} of the probe's {e1[probe][HYB]['all']['n_non_emergency']} non-emergencies (Figure {{H1_recall}}, Figure {{H2_tradeoff}}).",
    f"Add robustness: with realistic typing noise at level 0.3 the rules catch {f2(e3[hw]['all combined']['0.3']['rules']['emergency_recall'])} of emergencies, the hybrid {f2(e3[hw]['all combined']['0.3']['hybrid (rules + chars model)']['emergency_recall'])} (Figure {{H3_noise}}).",
    f"Add negation: applying the English cue direction to Hindi, Hinglish and Marathi causes {d6[ENG]['by_lang']['all']['dangerous']} dangerous errors against {d6[CUR]['by_lang']['all']['dangerous']} for the direction-aware rule (Figure {{S2_dangerous}}).",
    "Drop the clause about illustrations, or say they are original drawings and Wikimedia images; they are not an NLP result.",
])
h("2. Introduction")
p("In India the bystander at a collapse, snakebite or burn is often the only help for several minutes, and the first minutes decide the outcome. These people search in everyday words, in their own language and frequently in Hinglish, and many have heard remedies that cause harm, such as cutting a snakebite or putting toothpaste on a burn. A useful assistant must therefore understand informal multilingual text, recognise an emergency reliably, and never invent medical instructions.", "draft")
p("Our approach separates what must be exact from what can be learned. The first aid content is a small, hand-checked corpus of five procedure records, stored as branching steps with a source citation on every step, and translated by language owners. NLP components decide only which verified steps to show and when to raise an alarm. Every safety decision has a rule-based floor, so the system can become more cautious through a model but never less. The app runs fully on CPU and is deployed as a single container on Render.", "draft")
notes("Points you may add to the introduction", [
    "Related work to cite from the reference list: code-mixed Hindi–English NLP (Sasidhar et al., 2020; Sreelakshmi et al., 2020), Indian-language processing (Harish & Rangan, 2020), BERT-family models (Gardazi et al., 2025), cross-lingual embeddings for low-resource languages (Sindane et al., 2025), negation in clinical text (Chapman et al., 2001; Harkema et al., 2009), explainability (Adadi & Berrada, 2018).",
    "Check the Render deployment claim before keeping it.",
])

h("2.1 Research questions", 2)
add({"type": "table", "widths": [1500, 1300, 6560], "header": ["Student", "Language", "Question"], "rows": [
    ["Taneesha", "English", "How accurately can safety-critical facts and the situation be extracted from free text, and how large is the gap between English and the Indian languages?"],
    ["Atharva", "Hindi", "Can information-gain question selection resolve ambiguous reports within two questions, and does a trained character n-gram model identify Hindi, Marathi and Hinglish more reliably than word lists?"],
    ["Siddhi", "Marathi", "Can a direction-aware negation window handle Marathi's post-verbal negation, and can a cross-language pass stop a wrong language guess from hiding an emergency?"],
    ["Soham", "Hinglish", "Does the triage layer catch every emergency in every language, and can the alert explain itself using the user's own Hinglish spelling?"],
]})

h("2.2 Research contributions", 2)
for name, text in [
    ("Taneesha Badhe.", "Wrote the unresponsive and heart attack procedure records and the F1 extractor, which fills twelve slots (responsiveness, breathing, chest pain, choking signs, bite type, allergy signs, burn cause and area, power, age, time, actions taken) using per-language lexicons with typo-tolerant matching."),
    ("Atharva Hemade.", "Wrote the choking record and F2, which chooses the question with the highest expected entropy reduction over candidate situations and keeps per-session memory. Added a trained language identifier, speech input and the Hindi translation of all content."),
    ("Siddhi Karhekar.", "Wrote the bites record (snake, insect, scorpion, dog) and F3, which marks each fact as affirmed, negated or uncertain using cue lists and a three-token window searched first before the term (English, Hindi, Hinglish) or after it (Marathi). Added the cross-language safety net."),
    ("Soham Ghodake.", "Wrote the burns record (fire, chemical, electrical), the safety-rules floor and F4, which shows the exact words that triggered an alert, mapped back to the user's original spelling."),
]:
    add({"type": "p", "text": text, "lead": name, "style": "draft"})
notes("Contributions to add, one sentence or two per person", [
    "Taneesha: the comparison of rules against TF-IDF classifiers for situation identification, and the cross-lingual transfer experiment (English plus 0–100% target-language data).",
    "Atharva: calibration of situation confidence (reliability diagram, ECE) and the risk–coverage analysis behind the 0.75 question threshold.",
    "Siddhi: the negation diagnostic set, the comparison of cue-attachment rules (window sizes, English direction, ConText-style, proposed clause-wide uncertainty), and the 1,309-pair adversarial test set for the step verifier.",
    "Soham: the hybrid triage evaluation (rules floor + model), the robustness test with five kinds of typing noise, and the deletion-based faithfulness test of explanations.",
])

h("2.3 Methodology", 2)
add({"type": "table", "widths": [1500, 7860], "header": ["Person", "Description"], "rows": [
    ["Taneesha", "Lexicon entries map phrases to slot values; rapidfuzz (score ≥ 85) tolerates misspellings. A keyword-overlap score over the five records plus an out-of-scope class stands in for BGE-M3 until it is fine-tuned, behind the same interface."],
    ["Atharva", "Each question in the bank lists the answer expected under every candidate; the gain of a question is the drop in entropy it is expected to cause. Safety questions (responsiveness, breathing, power) always win when those facts are unknown. Language ID is TF-IDF over character 1–4-grams with multinomial logistic regression; the script decides first and the classifier chooses within it."],
    ["Siddhi", "Negation and uncertainty cues are attached to the nearest symptom term within three tokens in the language's usual direction; uncertain safety facts are dropped and trigger a question. The safety net re-runs extraction with the sibling language of the same script and keeps only urgency-raising facts from words the first pass did not read."],
    ["Soham", "Nineteen rules derived from the specification (for example: unresponsive or abnormal breathing, chest pain, any snakebite, any electrical injury) force an emergency; a triage model may only raise the result. F4 lists the rule trigger words; in real mode it will use attributions from IndicBERT v2."],
]})
notes("Evaluation method to add (shared by all four)", [
    "Classical baselines trained on train.jsonl (2,880 template messages): TF-IDF word 1–2-grams and character 2–5-grams with logistic regression (C = 10), and Naive Bayes (Salton & Buckley, 1988).",
    "Evaluation sets: dev (720 template), safety suite (103 team-written), probe (100 short, misspelt messages; silver labels to be checked by the team). The hand-written test set (Section 10 of the specification) is still to be written.",
    "95% bootstrap intervals (1,000 resamples) for accuracy and recall. Hybrid: emergency if the rules or the model say so.",
    "Noise: vowels dropped, typos, spelling variants, code-switching (a word swapped for the English word with the same slot in the lexicons), dropped words; levels 0–0.5, three seeds.",
])

# ------------------------------------------------------------------ corpora
h("2.4 Description of corpora", 2)
for lead, text in [
    ("Procedure corpus (all).", "Five JSON records with 68 steps, each step citing IFRC 2025, AHA/Red Cross 2024, AHA 2025 BLS, ILCOR 2025 or NAPSE, plus 29 do-not rules and 13 harmful-remedy myths. All 205 strings were translated into Hindi, Marathi and Hinglish; five steps carry Wikimedia Commons illustrations (CC BY-SA 4.0 / CC0)."),
    ("Query corpus (Taneesha, English).", "3,600 template messages, 720 train and 180 dev per language, balanced over the six classes and labelled with situation, subtype, urgency and slots (Figure 1). English messages are the longest, 11.0 words on average."),
    ("Hindi and Hinglish queries (Atharva, Soham).", "Hindi averages 9.9 words and Hinglish 9.7. Hinglish is written in natural romanised spelling (\"saans\", \"sans\", \"saas\"), not transliterated from Hindi."),
    ("Marathi queries and evaluation sets (Siddhi).", "Marathi is the most compact language at 7.8 words. Two extra sets test safety: a 103-case safety suite (85 must-be-emergency) and a 100-message probe set of short, misspelt, code-mixed messages. The probe set is never used for training, but its errors were used once to find lexicon gaps (Section 2.6)."),
]:
    add({"type": "p", "text": text, "lead": lead, "style": "draft"})
en, sf = e4["train (template)"], e4["safety suite"]
notes("Corpus facts to add (from docs/research/e4_corpus.md)", [
    f"Template data is narrow: 720 English template messages use {en['en']['vocabulary']} distinct words, while 30 team-written safety-suite messages use {sf['en']['vocabulary']}. In 24 random messages: template ≈{en['en']['vocab_per_24_messages']:.0f} distinct words, safety suite ≈{sf['en']['vocab_per_24_messages']:.0f} (English); Marathi {en['mr']['vocab_per_24_messages']:.0f} vs {sf['mr']['vocab_per_24_messages']:.0f}.",
    f"Hinglish Code-Mixing Index (Das & Gambäck, 2014 — ICON, not an allowed publisher; describe the formula without citing, or ask your guide): template {en['hinglish']['cmi_mean']:.1f} with {pc(en['hinglish']['share_code_mixed'])} of messages mixed; probe {e4['probe']['hinglish']['cmi_mean']:.1f} with {pc(e4['probe']['hinglish']['share_code_mixed'])}.",
    "Update: the illustrations sentence (there are now also original drawings and animations) and the probe description (machine-drafted, silver labels). New files: data/queries/probe_labelled.jsonl (situation and urgency labels for the probe), data/verifier/adversarial.jsonl (1,309 pairs), the negation diagnostic set (research/negation_frames.py).",
])
h("2.4.1 Corpus screenshots", 3)
fig("corpus_en", "Taneesha: English rows of the query corpus (train.jsonl) and the safety suite, screenshot of the data files")
fig("corpus_hi", "Atharva: Hindi rows of the query corpus (train.jsonl) and the safety suite")
fig("corpus_mr", "Siddhi: Marathi rows of the query corpus (train.jsonl) and the safety suite")
fig("corpus_hinglish", "Soham: Hinglish rows of the query corpus (train.jsonl) and the safety suite")

# ------------------------------------------------------------------ implementation
h("2.5 Implementation", 2)
add({"type": "table", "widths": [1400, 2700, 5260], "header": ["Person", "Component", "Details"], "rows": [
    ["Taneesha", "extractor (backend/app/extract.py)", "Runs on Unicode-normalised text with Devanagari digits mapped to 0–9 and feeds the situation classifier; the BGE-M3 fine-tuning notebook is ready but not yet trained."],
    ["Atharva", "language model (app/models/ngram_langid.py)", "Trained by scripts/train_langid.py on 3,907 sentences, has 9,489 features and ships as 481 KB of JSON with pure-Python inference. The mic button uses browser speech recognition and only fills the text box; the user always presses Continue."],
    ["Siddhi", "negation (app/negation.py)", "Lives in app/negation.py; the safety net is extract_safe in app/extract.py and is covered by ten tests. The mmBERT verifier notebook is ready; in stub mode every rephrasing is rejected, so users always see verified text."],
    ["Soham", "rules floor (app/safety_rules.py)", "Runs in both modes. The React frontend keeps \"Call 112\" visible on every screen and uses red only for emergency actions. 443 backend and 41 frontend tests pass."],
]})
notes("Implementation updates (the format asks each student to implement one recent NLP model on their corpus)", [
    "Each student's model is set up in Colab: training/03_verifier_mmbert.ipynb (Siddhi), 04_triage_indicbert.ipynb (Soham; MuRIL comparison), 05_research_transformers.ipynb (LaBSE / BGE-M3 / multilingual-E5 embeddings, fine-tuned MuRIL and IndicBERT v2, Integrated Gradients). Run them on a T4 GPU (about an hour) and add their rows to Figures 7, 23 and the tables; until then, say plainly which results are from classical models.",
    "Implemented and evaluated now: TF-IDF word and character models with logistic regression, Naive Bayes, the hybrid triage, the trained character n-gram language identifier, eight experiment scripts in backend/research/ (python -m research.report reruns all in about 9 minutes).",
    "Mic now detects the spoken language itself (POST /api/langid with the char n-gram model, switching the recogniser at ≥ 0.85 confidence); a read-aloud option speaks each step. Tests now: 448 backend, 59 frontend.",
])

# ------------------------------------------------------------------ results
h("2.6 Results", 2)
p("Results are reported per language on the dev set (template messages), the safety suite and the hand-written probe set. The probe set revealed missing phrasings, which we then added to the lexicons; where this matters, results are shown before and after that fix. Because the fix was chosen by looking at the probe errors, the after-fix probe numbers are optimistic, and the team's own hand-written test set remains the fair measure.", "draft")
notes("Fix in the paragraph above", [
    "Write \"the probe set\" instead of \"the hand-written probe set\": its 100 messages were drafted by the build tool, and its situation and urgency labels (probe_labelled.jsonl) are silver labels to be checked by the team.",
    "Figures below use the safety suite (team-written) and the probe; every figure caption says which.",
])
rows = []
rows.append(["Slot F1 (dev)"] + [f2(x["slot_f1"]["dev (template)"][l]) for l in L])
rows.append(["Situation accuracy (probe): before fix → after"] + [f"{f2(e1[probe][OLD][l]['situation_acc'][0])} → {f2(e1[probe]['rules'][l]['situation_acc'][0])}" for l in L])
rows.append(["Emergency recall (probe): rules before fix → hybrid"] + [f"{f2(e1[probe][OLD][l]['emergency_recall'][0])} → {f2(e1[probe][HYB][l]['emergency_recall'][0])}" for l in L])
lid = x["langid"]["accuracy"]["probe"]
rows.append(["Language ID (probe): rules → char n-gram"] + [f"{f2(lid['word-list rules'][l])} → {f2(lid['char n-gram model'][l])}" for l in L])
sn = x["safety_net"]
rows.append(["Missed emergencies, wrong language: plain → net"] + [f"{sn[l]['missed_plain']}/{sn[l]['n']} → {sn[l]['missed_net']}/{sn[l]['n']}" for l in L])
rows.append(["Negation fact accuracy: current rule"] + [f2(d6[CUR]["by_lang"][l]["accuracy"]) for l in L])
rows.append(["Emergency recall at noise 0.3: rules → hybrid (all languages)"] + [f"{f2(e3[hw]['all combined']['0.3']['rules']['emergency_recall'])} → {f2(e3[hw]['all combined']['0.3']['hybrid (rules + chars model)']['emergency_recall'])}", "", "", ""])
add({"type": "table", "widths": [3760, 1400, 1400, 1400, 1400], "header": ["Measure", "English", "Hindi", "Hinglish", "Marathi"], "rows": rows, "small": True,
     "caption": "Table 1. Summary of results per language"})

h("Taneesha — F1 extraction and situation identification", 3)
fig("T1_slot_f1", "Taneesha: F1 slot extraction, micro-F1 per language on the dev set")
fig("T2_situation_sets", "Taneesha: situation accuracy of the app on template, safety-suite and probe messages (95% bootstrap intervals)")
fig("T3_situation_models", "Taneesha: situation accuracy on the probe set, rules (before the lexicon fix) vs classical text classifiers")
fig("T4_confusion", f"Taneesha: situation confusion matrices on {x['confusion']['n']} safety-suite and probe messages")
fig("T5_transfer", "Taneesha: cross-lingual transfer from English; situation accuracy as target-language training data is added")
h("Atharva — F2 clarifying questions and language identification", 3)
fig("A1_langid", "Atharva: language identification accuracy, word-list rules vs trained character n-gram model")
fig("A2_langid_confusion", "Atharva: language identification confusion matrices on the 100-message probe set")
fig("A3_clarify", "Atharva: F2 clarifying questions, (a) ambiguous queries resolved within two questions, (b) share of safety-suite and probe messages that received a question")
fig("A4_reliability", "Atharva: reliability diagram of situation confidence on safety-suite and probe messages")
fig("A5_risk_coverage", "Atharva: risk–coverage curve; answering only above 0.75 confidence keeps the error rate low")
h("Siddhi — F3 negation, cross-language safety net and step verification", 3)
fig("S1_negation", "Siddhi: F3 negation and uncertainty accuracy per language for four cue-attachment rules")
fig("S2_dangerous", "Siddhi: dangerous negation errors (a negated or uncertain fact read as reassuring) for each cue-attachment rule")
fig("S3_frames", "Siddhi: accuracy of the current negation rule by sentence frame and language")
fig("S4_safety_net", "Siddhi: emergencies missed when the language is guessed wrong, without and with the cross-language safety net")
fig("S5_verifier", "Siddhi: adversarial test of lexical step verifiers, the baseline the mmBERT verifier must beat")
h("Soham — urgency triage and explainable alerts", 3)
fig("H1_recall", "Soham: emergency recall on the probe set per language; the model under the rules floor catches the emergencies the rules missed")
fig("H2_tradeoff", "Soham: probe set, missed emergencies against false alarms for each triage system")
fig("H3_noise", "Soham: robustness of triage to realistic typing noise on safety-suite and probe messages")
fig("H4_noise_types", "Soham: emergency recall by noise type at level 0.3")
fig("H5_faithfulness", "Soham: faithfulness of explanations, drop in emergency probability when the highlighted words are deleted")

# ------------------------------------------------------------------ discussion
h("2.7 Discussion", 2)
R = FIGREF
cf = x["confusion"]
notes("Taneesha (one paragraph; refer to Figures " + ", ".join(str(R[k]) for k in ("T1_slot_f1", "T2_situation_sets", "T3_situation_models", "T4_confusion", "T5_transfer")) + ")", [
    f"Slot F1 is {f2(x['slot_f1']['dev (template)']['en'])} in English and {f2(x['slot_f1']['dev (template)']['mr'])} in Marathi (largest gap, −{f2(x['slot_f1']['dev (template)']['en'] - x['slot_f1']['dev (template)']['mr'])}) (Figure {R['T1_slot_f1']}).",
    f"Template scores do not carry over: on the probe, situation accuracy of the rules before the fix was {', '.join(f'{LN[l]} {f2(e1[probe][OLD][l][chr(115)+'ituation_acc'][0])}' for l in L)} (Figure {R['T3_situation_models']}).",
    f"Confusion matrix (Figure {R['T4_confusion']}): the rules' only errors are {cf['rules'][2][0]} choking messages read as unresponsive; the template-trained model confuses out-of-scope messages most ({cf['model'][5][5]} of {sum(cf['model'][5])} correct).",
    f"Transfer (Figure {R['T5_transfer']}): English-only training gives {f2(e2['char']['hinglish']['0.0']['probe'][0])} on Hinglish (shared script, borrowed words such as chest, current, acid) and 0 on Hindi/Marathi; 5% target data (36 messages) reaches {f2(e2['char']['hi']['0.05']['probe'][0])}/{f2(e2['char']['hinglish']['0.05']['probe'][0])}/{f2(e2['char']['mr']['0.05']['probe'][0])}; the plateau on safety-suite and probe messages ({f2(e2['char']['mr']['1.0']['probe'][0])} for Marathi) stays below the 1.00 on template dev.",
])
cl = x["clarify"]
notes("Atharva (Figures " + ", ".join(str(R[k]) for k in ("A1_langid", "A2_langid_confusion", "A3_clarify", "A4_reliability", "A5_risk_coverage")) + ")", [
    f"Language ID (Figures {R['A1_langid']}–{R['A2_langid_confusion']}): word lists misread 2 Hinglish probe messages as English and 1 Marathi as Hindi; the char n-gram model gets all 100 right (examples: \"dadaji ko current laga\", \"लवकर सांगा\").",
    f"F2 (Figure {R['A3_clarify']}): all ambiguous dev queries are resolved within two questions (n = {sum(v['ambiguous'] for v in cl['resolution'].values())}); on safety-suite and probe messages the app asks a question for {pc(sum(v.get('question', 0) for v in cl['hand_written_asked'].values()) / sum(sum(v.values()) for v in cl['hand_written_asked'].values()))} of messages.",
    f"Calibration (Figure {R['A4_reliability']}): model ECE {e5['safety suite + probe']['model']['ece']:.3f}, app confidence ECE {e5['safety suite + probe']['rules (app confidence)']['ece']:.3f}.",
    f"Risk–coverage (Figure {R['A5_risk_coverage']}): above 0.75 confidence {pc(e5['safety suite + probe']['model']['threshold_0.75']['answered_share'])} of messages are answered at {f2(e5['safety suite + probe']['model']['threshold_0.75']['accuracy_answered'])} accuracy; below it accuracy is {f2(e5['safety suite + probe']['model']['threshold_0.75']['accuracy_questioned'])}, so asking there is justified.",
])
notes("Siddhi (Figures " + ", ".join(str(R[k]) for k in ("S1_negation", "S2_dangerous", "S3_frames", "S4_safety_net", "S5_verifier")) + ")", [
    f"Direction matters (Figures {R['S1_negation']}–{R['S2_dangerous']}): with the English rule (cue before the word) Hindi/Hinglish/Marathi fall to {f2(d6[ENG]['by_lang']['hi']['accuracy'])}/{f2(d6[ENG]['by_lang']['hinglish']['accuracy'])}/{f2(d6[ENG]['by_lang']['mr']['accuracy'])} and dangerous errors rise to {d6[ENG]['by_lang']['all']['dangerous']}; the direction-aware rule gives {f2(d6[CUR]['by_lang']['hi']['accuracy'])}/{f2(d6[CUR]['by_lang']['hinglish']['accuracy'])}/{f2(d6[CUR]['by_lang']['mr']['accuracy'])} with {d6[CUR]['by_lang']['all']['dangerous']}.",
    f"Where it fails (Figure {R['S3_frames']}): sentence-initial uncertainty (F03, F13) and long-scope negation (F08). \"not sure if my father is breathing\" is read as breathing normally because the uncertainty cue attaches to \"father\". Letting uncertainty cover every safety fact in its clause raises accuracy to {f2(d6[PROP]['by_lang']['all']['accuracy'])} with {d6[PROP]['by_lang']['all']['dangerous']} dangerous errors, with no change on the safety suite or probe. F08 (\"कोई दर्द या दबाव नहीं\") is a lexicon gap.",
    "Caveat: the diagnostic set was machine-drafted (65 sentences per language); confirm on the owners' 100-sentence sets.",
    f"Safety net (Figure {R['S4_safety_net']}): with the language forced wrong, missed emergencies fall from {sn['hi']['missed_plain']}/20 to 0 (Hindi), {sn['hinglish']['missed_plain']}/20 to 0 (Hinglish), {sn['mr']['missed_plain']}/20 to 0 (Marathi).",
    f"Verifier (Figure {R['S5_verifier']}): word overlap tuned to accept 95% of safe rewordings rejects only {pc(v7[VJ]['negation_removed'])} of steps with \"do not\" removed and {pc(v7[VJ]['number_changed'])} with a changed number; a hand-written guard catches those but misses {pc(1 - v7[VG]['antonym'])} of antonym swaps and rejects {pc(1 - v7[VG]['polite_form'])} of polite rewordings. This motivates the trained mmBERT verifier (add its row after notebook 05).",
])
c3 = e3[hw]["all combined"]["0.3"]
notes("Soham (Figures " + ", ".join(str(R[k]) for k in ("H1_recall", "H2_tradeoff", "H3_noise", "H4_noise_types", "H5_faithfulness")) + ")", [
    f"Hybrid (Figures {R['H1_recall']}–{R['H2_tradeoff']}): rules before the fix miss {e1[probe][OLD]['all']['missed_emergencies']} of {e1[probe][OLD]['all']['n_emergency']} probe emergencies; the hybrid misses {e1[probe][HYB]['all']['missed_emergencies']}, with false alarms {e1[probe][HYB]['all']['false_alarm_rate'][0]:.2f} vs {e1[probe][OLD]['all']['false_alarm_rate'][0]:.2f}. Models alone miss {e1[safety][WC]['all']['missed_emergencies']} safety-suite emergencies, so the rules floor stays essential.",
    f"Noise (Figures {R['H3_noise']}–{R['H4_noise_types']}): at level 0.3 rules recall {f2(c3['rules']['emergency_recall'])}, character model {f2(c3['model (chars)']['emergency_recall'])}, hybrid {f2(c3['hybrid (rules + chars model)']['emergency_recall'])}; dropped vowels ({f2(e3[hw]['vowel_drop']['0.3']['rules']['emergency_recall'])}) and dropped words ({f2(e3[hw]['fragment']['0.3']['rules']['emergency_recall'])}) hurt the rules most.",
    f"Explanations (Figure {R['H5_faithfulness']}): deleting the top-3 attributed words lowers P(emergency) by {f2(e8['word']['top3']['comprehensiveness'])} vs {f2(e8['word']['random3']['comprehensiveness'])} for random words; deleting the app's own trigger words removes the rule alert in {pc(e8['word']['rule_trigger_words']['rules_flip_rate'])} of emergencies, so in the rest the alert also fired on words F4 does not show.",
])

h("2.8 Conclusion", 2)
notes("One consolidated paragraph covering each member", [
    "Taneesha: extraction F1 0.94–0.99 on templates; the template-to-real gap and the cross-lingual transfer curve.",
    "Atharva: char n-gram language ID 1.00 on the probe; F2 resolves all ambiguous dev queries; the 0.75 threshold is supported by calibration.",
    "Siddhi: direction-aware negation prevents most dangerous errors; clause-wide uncertainty removes the rest; the safety net removes wrong-language misses; lexical verifiers are not enough.",
    "Soham: the rules floor plus a learned model catches emergencies the word lists miss and survives noise, at a false-alarm cost; F4 explanations need to show every trigger.",
    "Next: the hand-written test set with agreement (docs/annotation/GUIDELINES.md) and the transformer runs.",
])

# ------------------------------------------------------------------ references
h("2.9 References", 2)
refs = [
    "Adadi, A., & Berrada, M. (2018). Peeking inside the black-box: A survey on explainable artificial intelligence (XAI). IEEE Access, 6, 52138–52160. https://doi.org/10.1109/ACCESS.2018.2870052",
    "Chapman, W. W., Bridewell, W., Hanbury, P., Cooper, G. F., & Buchanan, B. G. (2001). A simple algorithm for identifying negated findings and diseases in discharge summaries. Journal of Biomedical Informatics, 34(5), 301–310. https://doi.org/10.1006/jbin.2001.1029",
    "Gardazi, N. M., Daud, A., Malik, M. K., Bukhari, A., Alsahfi, T., … Alshemaimri, B. (2025). BERT applications in natural language processing: A review. Artificial Intelligence Review, 58(6), Article 166. https://doi.org/10.1007/s10462-025-11162-5 [complete the author list from the article page]",
    "Harish, B. S., & Rangan, R. K. (2020). A comprehensive survey on Indian regional language processing. SN Applied Sciences, 2, Article 1204. https://doi.org/10.1007/s42452-020-2983-x",
    "Harkema, H., Dowling, J. N., Thornblade, T., & Chapman, W. W. (2009). ConText: An algorithm for determining negation, experiencer, and temporal status from clinical reports. Journal of Biomedical Informatics, 42(5), 839–851. https://doi.org/10.1016/j.jbi.2009.05.002",
    "Quinlan, J. R. (1986). Induction of decision trees. Machine Learning, 1(1), 81–106. https://doi.org/10.1007/BF00116251",
    "Salton, G., & Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. Information Processing & Management, 24(5), 513–523. https://doi.org/10.1016/0306-4573(88)90021-0",
    "Sasidhar, T. T., Premjith, B., & Soman, K. P. (2020). Emotion detection in Hinglish (Hindi+English) code-mixed social media text. Procedia Computer Science, 171, 1346–1352. https://doi.org/10.1016/j.procs.2020.04.144",
    "Sindane, T., Marivate, V., & Modupe, A. (2025). Cross-lingual embedding methods and applications: A systematic review for low-resourced scenarios. Natural Language Processing Journal, 12, Article 100157. https://doi.org/10.1016/j.nlp.2025.100157",
    "Sreelakshmi, K., Premjith, B., & Soman, K. P. (2020). Detection of hate speech text in Hindi-English code-mixed data. Procedia Computer Science, 171, 737–744. https://doi.org/10.1016/j.procs.2020.04.080",
]
for r in refs:
    add({"type": "ref", "text": r})
add({"type": "h", "text": "Corpora, guidelines and models (URLs)", "level": 3})
for r in [
    "Query corpus, safety suite, probe set, adversarial verifier pairs and code: https://github.com/atharva-1910/firstaid-assitant",
    "IFRC (2026). International First Aid, Resuscitation and Education Guidelines 2025. https://www.ifrc.org/media/78476",
    "AHA & American Red Cross (2024). Guidelines for First Aid. https://www.ahajournals.org/doi/10.1161/CIR.0000000000001281",
    "AHA (2025). Adult Basic Life Support. https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/adult-basic-life-support",
    "ILCOR (2025). International Consensus on First Aid Science. https://www.ilcor.org/uploads/FA-2025-COSTR-Full-Chapter.pdf",
    "MoHFW (2024). National Action Plan for Prevention and Control of Snakebite Envenoming. https://ncdc.mohfw.gov.in/wp-content/uploads/2024/07/NATIONAL-ACTION-PLAN-FOR-PREVENTION-AND-CONTROL-OF-SNAKEBITE-ENVENOMING-NAPSE.pdf",
    "IndicXNLI: https://huggingface.co/datasets/Divyanshu/indicxnli · XNLI: https://huggingface.co/datasets/facebook/xnli",
    "Models: https://huggingface.co/ai4bharat/IndicBERTv2-MLM-only · https://huggingface.co/google/muril-base-cased · https://huggingface.co/BAAI/bge-m3 · https://huggingface.co/jhu-clsp/mmBERT-base · https://huggingface.co/google/gemma-3-4b-it",
]:
    add({"type": "ref", "text": r})

# resolve {FIG} placeholders in notes
for b in blocks:
    if b["type"] == "notes":
        b["items"] = [it.replace("{H1_recall}", str(R["H1_recall"])).replace("{H2_tradeoff}", str(R["H2_tradeoff"])).replace("{H3_noise}", str(R["H3_noise"])).replace("{S2_dangerous}", str(R["S2_dangerous"])) for it in b["items"]]
        b["items"] = [it.replace("Figures 7, 23", f"Figures {R['T3_situation_models']}, {R['H1_recall']}") for it in b["items"]]
(ROOT / "report_spec.json").write_text(json.dumps(blocks, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(blocks), "blocks,", fignum[0], "figures")
