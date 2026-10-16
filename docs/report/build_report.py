"""Builds report_spec.json for the final CCA1 report (full text). Numbers come from docs/research/*.json.
Run: python build_report.py && node build_docx.js"""
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



def para(lead, text):
    add({"type": "p", "lead": lead, "text": text, "style": "body"})


# ------------------------------------------------------------------ numbers used in the text
pr_old, pr_hyb, pr_cur = e1[probe][OLD]["all"], e1[probe][HYB]["all"], e1[probe]["rules"]["all"]
sf_model = e1[safety][WC]["all"]
c3 = e3[hw]["all combined"]["0.3"]
sn = x["safety_net"]
slot = x["slot_f1"]["dev (template)"]
lid = x["langid"]["accuracy"]["probe"]
cl = x["clarify"]
asked = sum(v.get("question", 0) for v in cl["hand_written_asked"].values()) / sum(sum(v.values()) for v in cl["hand_written_asked"].values())
amb = sum(v["ambiguous"] for v in cl["resolution"].values())
m5 = e5[hw]["model"]
r5 = e5[hw]["rules (app confidence)"]
tr = lambda t, f: e2["char"][t][f]["probe"][0]  # noqa: E731
cf = x["confusion"]
en4, sf4, pb4 = e4["train (template)"], e4["safety suite"], e4["probe"]

# ------------------------------------------------------------------ front matter
add({"type": "title", "text": "Multilingual First Aid Assistant"})
add({"type": "subtitle", "text": "CCA1 Report · CCNLP Mini Project · MIT World Peace University, Pune"})
add({"type": "table", "widths": [1900, 1350, 1150, 2200, 2760], "header": ["Name", "PRN", "Language", "Feature", "Model"], "rows": [
    ["Taneesha Badhe", "1032232190", "English", "F1 detail extraction", "TF-IDF situation classifiers; BGE-M3 (set up)"],
    ["Atharva Hemade", "1032232249", "Hindi", "F2 clarifying question, memory", "Character n-gram language identifier"],
    ["Siddhi Karhekar", "1032232132", "Marathi", "F3 negation and uncertainty", "Negation scope rules; mmBERT verifier (set up)"],
    ["Soham Ghodake", "1032232337", "Hinglish", "F4 explainable alert", "Hybrid TF-IDF triage; IndicBERT v2 (set up)"],
]})
para("Problem statement.", "Bystanders who help an injured adult before the ambulance arrives are usually untrained, describe the scene in their own language, and often follow harmful home remedies. Existing first aid datasets are English-only question–answer lists without step order or sources, and general chatbots do not cite guidelines or get tested for safety in Indian languages. There is no first aid resource that is structured, source-cited, multilingual (including code-mixed Hinglish) and tested for safety at the same time.")

# ------------------------------------------------------------------ 1 abstract
h("1. Abstract")
p(f"Bystanders who help an injured adult before an ambulance arrives describe the scene in everyday, often code-mixed language. We present a first aid assistant for English, Hindi, Hinglish and Marathi that covers five adult emergencies and never generates medical text: every step comes from a hand-checked, source-cited procedure corpus. An NLP pipeline identifies the language with a trained character n-gram model, extracts twelve safety facts with direction-aware negation, applies a rule-based urgency floor that a model may raise but never lower, and asks at most two information-gain questions when unsure. We built a 3,600-message query corpus, a 103-case safety suite and a 100-message probe set of short, misspelt messages. Before lexicon fixes the rules missed {pr_old['missed_emergencies']} of {pr_old['n_emergency']} probe emergencies; a TF-IDF classifier trained only on template data, placed under the rules floor, caught all of them at the cost of more false alarms. Under realistic typing noise, emergency recall of the rules fell to {f2(c3['rules']['emergency_recall'])} while the hybrid kept {f2(c3['hybrid (rules + chars model)']['emergency_recall'])}. Using English negation direction for the Indian languages caused {d6[ENG]['by_lang']['all']['dangerous']} dangerous errors against {d6[CUR]['by_lang']['all']['dangerous']} for our direction-aware rule, and a cross-language safety net removed every missed emergency under a wrong language guess.")

# ------------------------------------------------------------------ 2 introduction
h("2. Introduction")
p("In India the bystander at a collapse, snakebite or burn is often the only help for several minutes, and the first minutes decide the outcome. These people search in everyday words, in their own language and frequently in Hinglish, and many have heard remedies that cause harm, such as cutting a snakebite or putting toothpaste on a burn. A useful assistant must therefore understand informal multilingual text, recognise an emergency reliably, and never invent medical instructions.")
p("Work on code-mixed Hindi–English has mostly addressed social-media tasks such as emotion and hate-speech detection (Sasidhar et al., 2020; Sreelakshmi et al., 2020), and surveys of Indian-language processing point to the shortage of labelled data outside English (Harish & Rangan, 2020). Clinical NLP has long treated negation as a core problem (Chapman et al., 2001; Harkema et al., 2009), but its rules were designed for English, where the cue comes before the word it negates. Our approach separates what must be exact from what can be learned. The first aid content is a small, hand-checked corpus of five procedure records with a source citation on every step; NLP components only decide which verified steps to show and when to raise an alarm, and every safety decision has a rule-based floor. We evaluate each component per language, compare the rules with trained classifiers, and test robustness to the noisy, mixed-language text that people actually type in an emergency.")

h("2.1 Research questions", 2)
add({"type": "table", "widths": [1400, 1200, 6760], "header": ["Student", "Language", "Question"], "rows": [
    ["Taneesha", "English", "How accurately can safety-critical facts and the situation be extracted from free text, how large is the gap between English and the Indian languages, and how much target-language data closes it?"],
    ["Atharva", "Hindi", "Can information-gain question selection resolve ambiguous reports within two questions, does a trained character n-gram model identify the four languages more reliably than word lists, and is the confidence threshold for asking well placed?"],
    ["Siddhi", "Marathi", "Can a direction-aware negation rule handle Marathi's post-verbal negation, can a cross-language pass stop a wrong language guess from hiding an emergency, and can surface overlap verify a rephrased step?"],
    ["Soham", "Hinglish", "Does the triage layer catch every emergency in every language, including under noisy typing, and are the words shown as the reason for an alert faithful to the decision?"],
]})

h("2.2 Research contributions", 2)
para("Taneesha Badhe.", "Wrote the unresponsive and heart attack procedure records and the F1 extractor, which fills twelve slots (responsiveness, breathing, chest pain, choking signs, bite type, allergy signs, burn cause and area, power, age, time and actions taken) using per-language lexicons with typo-tolerant matching. She compared the rule-based situation identifier with TF-IDF classifiers and measured cross-lingual transfer from English to Hindi, Hinglish and Marathi.")
para("Atharva Hemade.", "Wrote the choking record and F2, which chooses the question with the highest expected entropy reduction over candidate situations and keeps per-session memory. He trained the character n-gram language identifier, built speech input that detects the spoken language, translated the content into Hindi, and analysed calibration and selective prediction for the decision to ask a question.")
para("Siddhi Karhekar.", "Wrote the bites record (snake, insect, scorpion, dog) and F3, which marks each fact as affirmed, negated or uncertain using cue lists and a window searched in each language's usual direction, and the cross-language safety net. She built a negation diagnostic set, compared seven cue-attachment strategies, proposed a clause-wide scope for uncertainty, and built a 1,309-pair adversarial test set for step verification.")
para("Soham Ghodake.", "Wrote the burns record (fire, chemical, electrical), the safety-rules floor and F4, which shows the exact words that triggered an alert in the user's own spelling. He evaluated hybrid triage (rules plus a trained classifier), its robustness to five kinds of typing noise, and the faithfulness of explanations with a deletion test.")

h("2.3 Methodology", 2)
para("Taneesha.", "Each lexicon entry maps phrases to slot values, and rapidfuzz matching (score ≥ 85) tolerates misspellings. The situation is scored by keyword overlap over the five records plus an out-of-scope class, behind the interface a fine-tuned BGE-M3 model will use. For comparison, TF-IDF classifiers (word 1–2-grams and character 2–5-grams with logistic regression, and Naive Bayes) are trained on the 2,880 template training messages; such baselines remain competitive in recent text-classification benchmarks (Reusens et al., 2024). Transfer, a central question for low-resource languages (Sindane et al., 2025), is measured by training on all English data plus 0, 5, 10, 25, 50 or 100% of one target language, averaged over three random subsamples. All intervals are 95% bootstrap intervals over 1,000 resamples.")
para("Atharva.", "Each question in the bank lists the answer expected under every candidate situation; its gain is the expected drop in entropy over the candidates, so the system asks the question most likely to resolve an ambiguous report, a problem also studied for clarification in multi-turn conversation (Shao et al., 2022). Safety questions (responsiveness, breathing, power) always win when those facts are unknown. Language identification uses TF-IDF over character 1–4-grams with multinomial logistic regression: the script decides first (Devanagari or Latin) and the classifier chooses within it. Calibration is measured with a reliability diagram and expected calibration error over ten bins, and selective prediction with a risk–coverage curve, in which only the most confident share of messages is answered without a question.")
para("Siddhi.", "Negation and uncertainty cues attach to the nearest symptom term within three tokens in the language's usual direction (before the word in English, after it in Hindi, Hinglish and Marathi); uncertain safety facts are dropped and trigger a question. A diagnostic set of 13 sentence frames × 5 people per language (260 sentences) covers plain and long-distance negation, uncertainty, and two facts with and without a scope breaker such as \"lekin\" or \"पण\". The same extractor is run with only the cue-attachment step changed: windows of 1, 3 and 6 tokens, an English-only direction, a ConText-style clause scope (Harkema et al., 2009), and a proposed rule in which uncertainty covers every safety fact in its clause. The safety net re-runs extraction with the sibling language of the same script and keeps only urgency-raising facts. For step verification, adversarial pairs are built from every step by removing or adding negation, changing numbers, dropping the call to 112 and swapping antonyms, with polite rewordings as safe controls.")
para("Soham.", "Nineteen rules from the specification (for example unresponsive or abnormal breathing, chest pain, any snakebite, any electrical injury) force an emergency. The hybrid triage flags a message when either the rules or a TF-IDF classifier does, so a model can only raise urgency. Robustness is tested by adding dropped vowels, typos, spelling variants, code-switching and dropped words to the safety-suite and probe messages at levels 0.1 to 0.5 with three random seeds. Explanation faithfulness is measured by deleting the words with the highest attribution and comparing the drop in predicted emergency probability with deleting random words, a standard check of whether an explanation reflects what the model actually used (Ali et al., 2023).")

# ------------------------------------------------------------------ 2.4 corpora
h("2.4 Description of corpora", 2)
para("Procedure corpus (all).", "Five JSON records with 68 steps, each step citing IFRC 2025, AHA/Red Cross 2024, AHA 2025 BLS, ILCOR 2025 or NAPSE, plus 29 do-not rules and 13 harmful-remedy myths. All 205 strings are translated into Hindi, Marathi and Hinglish.")
para("Query corpus (Taneesha, English).", f"3,600 template messages, 720 train and 180 dev per language, balanced over six classes and labelled with situation, subtype, urgency and slots (Figure 1). English messages are the longest at 11.0 words. Templates are narrow: the 720 English training messages use only {en4['en']['vocabulary']} distinct words, while the 30 team-written safety-suite messages use {sf4['en']['vocabulary']}.")
para("Hindi queries and the probe set (Atharva).", f"Hindi averages 9.9 words (Figure 2). The 100-message probe set was drafted by the build tool to be short, misspelt and code-mixed, 25 per language, and labelled with situation and urgency following the specification's rules (silver labels). It is never used for training; its errors were used once to find lexicon gaps, so results are also shown for the rules before that fix.")
para("Marathi queries and safety sets (Siddhi).", "Marathi is the most compact language at 7.8 words per message (Figure 3). The team wrote a 103-case safety suite (85 must-be-emergency) across the four languages. Two further sets test F3: the 260-sentence negation diagnostic set and 1,309 verifier pairs generated from the step texts in all four languages.")
para("Hinglish queries (Soham).", f"Hinglish averages 9.7 words and is written in natural romanised spelling (\"saans\", \"sans\", \"saas\"), not transliterated from Hindi (Figure 4). Its Code-Mixing Index, 100 × (1 − dominant-language words ÷ language words) per message, is {en4['hinglish']['cmi_mean']:.1f} for templates with {pc(en4['hinglish']['share_code_mixed'])} of messages mixed, and {pb4['hinglish']['cmi_mean']:.1f} for the probe with {pc(pb4['hinglish']['share_code_mixed'])} mixed.")
h("2.4.1 Corpus screenshots", 3)
fig("corpus_en", "Taneesha: English rows of the query corpus (train.jsonl) and the safety suite")
fig("corpus_hi", "Atharva: Hindi rows of the query corpus (train.jsonl) and the safety suite")
fig("corpus_mr", "Siddhi: Marathi rows of the query corpus (train.jsonl) and the safety suite")
fig("corpus_hinglish", "Soham: Hinglish rows of the query corpus (train.jsonl) and the safety suite")

# ------------------------------------------------------------------ 2.5 implementation
h("2.5 Implementation", 2)
para("Taneesha.", "The extractor (backend/app/extract.py) runs on Unicode-normalised text with Devanagari digits mapped to 0–9 and feeds the situation classifier. The TF-IDF classifiers are scikit-learn pipelines trained in backend/research/e1_models.py, and the transfer curves come from e2_transfer.py. Fine-tuning of BGE-M3 and other BERT-family encoders (Gardazi et al., 2025) is set up in training/05_research_transformers.ipynb; those runs need a GPU and are not included in the results below.")
para("Atharva.", "The language identifier (app/models/ngram_langid.py) is trained by scripts/train_langid.py on 3,907 sentences, has 9,489 features and ships as 481 KB of JSON with pure-Python inference. It is exposed as POST /api/langid, which the microphone uses to switch the browser's speech recogniser to the language being spoken when the model is at least 85% sure. F2 lives in app/clarify.py and app/memory.py, and the calibration analysis in research/e5_calibration.py.")
para("Siddhi.", "Negation is in app/negation.py and the safety net is extract_safe in app/extract.py. The diagnostic set and the six cue-attachment variants are in research/negation_frames.py and e6_negation.py, which swap only the attachment step of the real extractor. The adversarial pairs are written to data/verifier/adversarial.jsonl by e7_verifier.py, which also scores word-overlap and character F-score verifiers. The mmBERT verifier fine-tuned on XNLI and IndicXNLI is set up in training/03_verifier_mmbert.ipynb; in the app every rephrasing is rejected until it is trained, so users always see verified text.")
para("Soham.", "The rules floor (app/safety_rules.py) runs in both model modes, and the React frontend keeps \"Call 112\" on every screen. The hybrid triage, noise generators and faithfulness test are in research/e1_models.py, noise.py, e3_robustness.py and e8_faithfulness.py; IndicBERT v2 fine-tuning with Integrated Gradients is set up in training/04 and 05. The backend has 448 automated tests and the frontend 59, all passing; python -m research.report reproduces every result in about nine minutes.")

# ------------------------------------------------------------------ 2.6 results
h("2.6 Results", 2)
p("Results are reported per language on the dev set (template messages), the team-written safety suite and the probe set. Because the lexicons were later corrected by reading the probe errors, probe results are shown for the rules both before and after that fix. Table 1 summarises the main measures; Figures 5–24 give five results per student.")
rows = []
rows.append(["Slot F1 (dev)"] + [f2(slot[l]) for l in L])
rows.append(["Situation accuracy (probe): before fix → after"] + [f"{f2(e1[probe][OLD][l]['situation_acc'][0])} → {f2(e1[probe]['rules'][l]['situation_acc'][0])}" for l in L])
rows.append(["Emergency recall (probe): rules before fix → hybrid"] + [f"{f2(e1[probe][OLD][l]['emergency_recall'][0])} → {f2(e1[probe][HYB][l]['emergency_recall'][0])}" for l in L])
rows.append(["Language ID (probe): word lists → char n-gram"] + [f"{f2(lid['word-list rules'][l])} → {f2(lid['char n-gram model'][l])}" for l in L])
rows.append(["Missed emergencies, wrong language: plain → net"] + [f"{sn[l]['missed_plain']}/{sn[l]['n']} → {sn[l]['missed_net']}/{sn[l]['n']}" for l in L])
rows.append(["Negation fact accuracy: current → proposed rule"] + [f"{f2(d6[CUR]['by_lang'][l]['accuracy'])} → {f2(d6[PROP]['by_lang'][l]['accuracy'])}" for l in L])
add({"type": "table", "widths": [3760, 1400, 1400, 1400, 1400], "header": ["Measure", "English", "Hindi", "Hinglish", "Marathi"], "rows": rows, "small": True,
     "caption": "Table 1. Summary of results per language"})
h("Taneesha — F1 extraction and situation identification", 3)
fig("T1_slot_f1", "Taneesha: F1 slot extraction, micro-F1 per language on the dev set")
fig("T2_situation_sets", "Taneesha: situation accuracy of the app on template, safety-suite and probe messages (95% bootstrap intervals)")
fig("T3_situation_models", "Taneesha: situation accuracy on the probe set, rules (before the lexicon fix) vs classical text classifiers")
fig("T4_confusion", f"Taneesha: situation confusion matrices on {cf['n']} safety-suite and probe messages")
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
fig("S5_verifier", "Siddhi: adversarial test of lexical step verifiers, the baseline a trained verifier must beat")
h("Soham — urgency triage and explainable alerts", 3)
fig("H1_recall", "Soham: emergency recall on the probe set per language; the model under the rules floor catches the emergencies the rules missed")
fig("H2_tradeoff", "Soham: probe set, missed emergencies against false alarms for each triage system")
fig("H3_noise", "Soham: robustness of triage to realistic typing noise on safety-suite and probe messages")
fig("H4_noise_types", "Soham: emergency recall by noise type at level 0.3")
fig("H5_faithfulness", "Soham: faithfulness of explanations, drop in emergency probability when the highlighted words are deleted")
R = FIGREF

# ------------------------------------------------------------------ 2.7 discussion
h("2.7 Discussion", 2)
para("Taneesha.", f"Figure {R['T1_slot_f1']} shows slot F1 above 0.94 in every language, with the largest gap for Marathi ({f2(slot['mr'])} against {f2(slot['en'])} for English), whose compact verb forms are harder to match. Figure {R['T2_situation_sets']} shows that perfect template scores do not carry over to the probe, and Figure {R['T3_situation_models']} that before the lexicon fix the rules reached only {f2(e1[probe][OLD]['hinglish']['situation_acc'][0])} on Hinglish probe messages, where TF-IDF classifiers reached {f2(e1[probe]['TF-IDF words (1-2) + LR']['hinglish']['situation_acc'][0])}. The confusion matrices in Figure {R['T4_confusion']} show that the rules' only errors are {cf['rules'][2][0]} choking messages read as unresponsive, while the template-trained classifier struggles most with out-of-scope messages ({cf['model'][5][5]} of {sum(cf['model'][5])} correct). Figure {R['T5_transfer']} answers the transfer question: English data alone gives {f2(tr('hinglish', '0.0'))} on Hinglish, thanks to the shared script and borrowed words such as \"chest\", \"current\" and \"acid\", but nothing on Hindi or Marathi; adding only 5% of target-language data (36 messages) lifts them to {f2(tr('hi', '0.05'))} and {f2(tr('mr', '0.05'))}. Even with all the data, accuracy on probe messages stays at {f2(tr('mr', '1.0'))} for Marathi against 1.00 on template dev, which shows the template-to-real gap that a hand-written test set must measure.")
para("Atharva.", f"Figures {R['A1_langid']} and {R['A2_langid_confusion']} show that word lists misread two Hinglish probe messages as English and one Marathi message as Hindi (for example \"dadaji ko current laga\" and \"लवकर सांगा\"), while the character n-gram model identifies all 100 correctly at no runtime cost. Figure {R['A3_clarify']} shows that every one of the {amb} ambiguous dev queries is resolved within two questions, above the 90% target, and that on safety-suite and probe messages the app asks a question for {pc(asked)} of messages. The reliability diagram in Figure {R['A4_reliability']} shows the classifier's confidence is well calibrated (ECE {m5['ece']:.3f}), and Figure {R['A5_risk_coverage']} shows why the 0.75 threshold is sound: the {pc(m5['threshold_0.75']['answered_share'])} of messages above it are {f2(m5['threshold_0.75']['accuracy_answered'])} correct, while those below it are only {f2(m5['threshold_0.75']['accuracy_questioned'])} correct, so asking a question there is the right decision.")
para("Siddhi.", f"Figures {R['S1_negation']} and {R['S2_dangerous']} show that negation direction matters: applying the English rule (cue before the word) to Hindi, Hinglish and Marathi drops fact accuracy to {f2(d6[ENG]['by_lang']['hi']['accuracy'])}, {f2(d6[ENG]['by_lang']['hinglish']['accuracy'])} and {f2(d6[ENG]['by_lang']['mr']['accuracy'])} with {d6[ENG]['by_lang']['all']['dangerous']} dangerous errors, while the direction-aware rule reaches {f2(d6[CUR]['by_lang']['hi']['accuracy'])}, {f2(d6[CUR]['by_lang']['hinglish']['accuracy'])} and {f2(d6[CUR]['by_lang']['mr']['accuracy'])} with {d6[CUR]['by_lang']['all']['dangerous']}. Figure {R['S3_frames']} locates the remaining errors: uncertainty at the start of a sentence and in \"not sure if my father is breathing\", where the cue attaches to the nearest word (\"father\") instead of the safety fact. Letting uncertainty cover every safety fact in its clause raises accuracy to {f2(d6[PROP]['by_lang']['all']['accuracy'])} with no dangerous errors and no change on the safety suite or probe; the last misses (\"कोई दर्द या दबाव नहीं\") are lexicon gaps. Figure {R['S4_safety_net']} shows the safety net cutting missed emergencies under a wrong language guess from {sn['hi']['missed_plain']}/20, {sn['hinglish']['missed_plain']}/20 and {sn['mr']['missed_plain']}/20 to zero. Figure {R['S5_verifier']} shows that surface overlap cannot verify a rephrased step: word overlap tuned to accept 95% of safe rewordings rejects only {pc(v7[VJ]['negation_removed'])} of steps with \"do not\" removed and {pc(v7[VJ]['number_changed'])} with a changed number, which motivates the trained mmBERT verifier.")
para("Soham.", f"Figure {R['H1_recall']} shows that before the lexicon fix the rules missed {pr_old['missed_emergencies']} of {pr_old['n_emergency']} probe emergencies, and a TF-IDF classifier trained only on template data, placed under the rules floor, catches all of them without any lexicon change. Figure {R['H2_tradeoff']} shows the cost: the hybrid flags {pc(pr_hyb['false_alarm_rate'][0])} of the {pr_hyb['n_non_emergency']} probe non-emergencies against none for the rules, and models alone miss {sf_model['missed_emergencies']} safety-suite emergencies, so the rules floor remains essential. Figures {R['H3_noise']} and {R['H4_noise_types']} show the strongest case for the model: with all noise types at level 0.3, emergency recall of the rules falls to {f2(c3['rules']['emergency_recall'])}, while the character model keeps {f2(c3['model (chars)']['emergency_recall'])} and the hybrid {f2(c3['hybrid (rules + chars model)']['emergency_recall'])}; dropped vowels and dropped words hurt the rules most. Figure {R['H5_faithfulness']} shows that the classifier's highlighted words are faithful (deleting the top three lowers emergency probability by {f2(e8['word']['top3']['comprehensiveness'])} against {f2(e8['word']['random3']['comprehensiveness'])} for random words), but deleting the app's own trigger words removes the rule alert in only {pc(e8['word']['rule_trigger_words']['rules_flip_rate'])} of emergencies, so F4 should show every word that fired a rule.")

h("2.8 Conclusion", 2)
p(f"We built a multilingual first aid assistant that never generates medical text and keeps a rule-based safety floor under every model, and we measured where its language understanding holds and where it breaks. Taneesha's extractor reaches slot F1 of 0.94–0.99 on template data, and her transfer study shows that Hindi and Marathi need a small amount of their own data while Hinglish borrows from English. Atharva's character n-gram identifier recognises all four languages on the probe set, F2 resolves every ambiguous dev query within two questions, and calibration supports the 0.75 threshold for asking. Siddhi's direction-aware negation avoids most of the dangerous errors that English rules make in the Indian languages, her proposed clause-wide uncertainty scope removes the rest on the diagnostic set, and the cross-language safety net removes wrong-language misses. Soham's evaluation shows that a learned model under the rules floor catches emergencies the word lists miss and keeps catching them under noisy typing, at the cost of more false alarms, and that alert explanations must show every trigger. The next steps are a hand-written test set with inter-annotator agreement and the transformer models already set up, whose results will replace the classical baselines reported here.")

# ------------------------------------------------------------------ 2.9 references
h("2.9 References", 2)
for r in [
    "Ali, S., Abuhmed, T., El-Sappagh, S., Muhammad, K., Alonso-Moral, J. M., Confalonieri, R., Guidotti, R., Del Ser, J., Díaz-Rodríguez, N., & Herrera, F. (2023). Explainable artificial intelligence (XAI): What we know and what is left to attain trustworthy artificial intelligence. Information Fusion, 99, Article 101805. https://doi.org/10.1016/j.inffus.2023.101805",
    "Chapman, W. W., Bridewell, W., Hanbury, P., Cooper, G. F., & Buchanan, B. G. (2001). A simple algorithm for identifying negated findings and diseases in discharge summaries. Journal of Biomedical Informatics, 34(5), 301–310. https://doi.org/10.1006/jbin.2001.1029",
    "Gardazi, N. M., Daud, A., Malik, M. K., Bukhari, A., Alsahfi, T., & Alshemaimri, B. (2025). BERT applications in natural language processing: A review. Artificial Intelligence Review, 58(6), Article 166. https://doi.org/10.1007/s10462-025-11162-5",
    "Harish, B. S., & Rangan, R. K. (2020). A comprehensive survey on Indian regional language processing. SN Applied Sciences, 2, Article 1204. https://doi.org/10.1007/s42452-020-2983-x",
    "Harkema, H., Dowling, J. N., Thornblade, T., & Chapman, W. W. (2009). ConText: An algorithm for determining negation, experiencer, and temporal status from clinical reports. Journal of Biomedical Informatics, 42(5), 839–851. https://doi.org/10.1016/j.jbi.2009.05.002",
    "Reusens, M., Stevens, A., Tonglet, J., De Smedt, J., Verbeke, W., vanden Broucke, S., & Baesens, B. (2024). Evaluating text classification: A benchmark study. Expert Systems with Applications, 254, Article 124302. https://doi.org/10.1016/j.eswa.2024.124302",
    "Sasidhar, T. T., Premjith, B., & Soman, K. P. (2020). Emotion detection in Hinglish (Hindi+English) code-mixed social media text. Procedia Computer Science, 171, 1346–1352. https://doi.org/10.1016/j.procs.2020.04.144",
    "Shao, T., Cai, F., Chen, W., & Chen, H. (2022). Self-supervised clarification question generation for ambiguous multi-turn conversation. Information Sciences, 587, 626–641. https://doi.org/10.1016/j.ins.2021.12.040",
    "Sindane, T., Marivate, V., & Modupe, A. (2025). Cross-lingual embedding methods and applications: A systematic review for low-resourced scenarios. Natural Language Processing Journal, 12, Article 100157. https://doi.org/10.1016/j.nlp.2025.100157",
    "Sreelakshmi, K., Premjith, B., & Soman, K. P. (2020). Detection of hate speech text in Hindi-English code-mixed data. Procedia Computer Science, 171, 737–744. https://doi.org/10.1016/j.procs.2020.04.080",
]:
    add({"type": "ref", "text": r})
add({"type": "h", "text": "Corpora, guidelines and models (URLs)", "level": 3})
for r in [
    "Query corpus, safety suite, probe set, verifier pairs and code: https://github.com/atharva-1910/firstaid-assitant",
    "IFRC (2026). International First Aid, Resuscitation and Education Guidelines 2025. https://www.ifrc.org/media/78476",
    "AHA & American Red Cross (2024). Guidelines for First Aid. https://www.ahajournals.org/doi/10.1161/CIR.0000000000001281",
    "AHA (2025). Adult Basic Life Support. https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/adult-basic-life-support",
    "ILCOR (2025). International Consensus on First Aid Science. https://www.ilcor.org/uploads/FA-2025-COSTR-Full-Chapter.pdf",
    "MoHFW (2024). National Action Plan for Prevention and Control of Snakebite Envenoming. https://ncdc.mohfw.gov.in/wp-content/uploads/2024/07/NATIONAL-ACTION-PLAN-FOR-PREVENTION-AND-CONTROL-OF-SNAKEBITE-ENVENOMING-NAPSE.pdf",
    "IndicXNLI: https://huggingface.co/datasets/Divyanshu/indicxnli · XNLI: https://huggingface.co/datasets/facebook/xnli",
    "Models: https://huggingface.co/ai4bharat/IndicBERTv2-MLM-only · https://huggingface.co/BAAI/bge-m3 · https://huggingface.co/jhu-clsp/mmBERT-base · https://huggingface.co/google/muril-base-cased",
]:
    add({"type": "ref", "text": r})

(ROOT / "report_spec.json").write_text(json.dumps(blocks, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(blocks), "blocks,", fignum[0], "figures")
