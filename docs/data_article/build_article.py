"""Fills the Elsevier Data in Brief template with the data article for this repository.

    backend/.venv/bin/python docs/data_article/analyze_data.py           # statistics and figures
    backend/.venv/bin/python docs/data_article/build_article.py TEMPLATE.docx OUT.docx

TEMPLATE.docx is Elsevier's "data article template v.19". The script removes the instruction page,
instruction text, comment boxes and editing locks, keeps the template's header, styles and
specifications table, and writes every section. Numbers come from figures/stats.json.
"""
import copy
import json
import sys
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = Path(__file__).resolve().parent
FIG = HERE / "figures"
S = json.loads((FIG / "stats.json").read_text(encoding="utf-8"))
TEMPLATE, OUT = sys.argv[1], sys.argv[2]
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
n = lambda x: f"{x:,}"  # noqa: E731
pct = lambda a, b: f"{100 * a / b:.1f}%"  # noqa: E731

doc = docx.Document(TEMPLATE)
body = doc.element.body

# ---------------------------------------------------------------- clean the template
for tag in ("commentRangeStart", "commentRangeEnd", "permStart", "permEnd"):
    for el in list(body.iter(W + tag)):
        el.getparent().remove(el)
for ref in list(body.iter(W + "commentReference")):
    run = ref.getparent()
    run.getparent().remove(run)
for rel in list(doc.part.rels.values()):
    if any(k in rel.reltype for k in ("/comments", "commentsExtended", "commentsIds", "commentsExtensible", "/people")):
        doc.part.drop_rel(rel.rId)
prot = doc.settings.element.find(W + "documentProtection")
if prot is not None:
    doc.settings.element.remove(prot)

# Bullet formatting from the template's own list paragraphs.
list_ppr = next(copy.deepcopy(p._p.pPr) for p in doc.paragraphs if p.style.name == "List Paragraph")


def heading_paragraphs():
    return [p for p in doc.paragraphs if p.style.name == "Heading 1"]


def clear_after(heading_p, keep_tables=False):
    """Remove every block between a heading and the next heading (optionally keeping tables)."""
    el = heading_p._p.getnext()
    while el is not None and el.tag != W + "sectPr":
        if el.tag == W + "p":
            st = el.find(W + "pPr/" + W + "pStyle")
            if st is not None and st.get(W + "val") in ("Heading1", "Heading 1"):
                break
        nxt = el.getnext()
        if not (keep_tables and el.tag == W + "tbl"):
            el.getparent().remove(el)
        el = nxt


# Remove the instruction page: everything before ARTICLE INFORMATION.
first = next(p for p in heading_paragraphs() if p.text.strip().upper() == "ARTICLE INFORMATION")
for el in list(body):
    if el is first._p:
        break
    if el.tag != W + "sectPr":
        body.remove(el)
heads = {p.text.split("\n")[0].strip().upper(): p for p in heading_paragraphs()}
for hp in heads.values():  # drop instruction text that follows a line break inside a heading
    br = next(hp._p.iter(W + "br"), None)
    if br is not None:
        run = br.getparent()
        for sib in list(run.itersiblings()):
            if sib.tag == W + "r":
                sib.getparent().remove(sib)
        for el in list(run):
            if el.tag != W + "rPr" and (el is br or el.getprevious() is not None and list(run).index(el) > list(run).index(br)):
                run.remove(el)
for name, hp in heads.items():
    clear_after(hp, keep_tables=(name == "SPECIFICATIONS TABLE"))


# ---------------------------------------------------------------- writers
class Cursor:
    def __init__(self, after):
        self.el = after._p if hasattr(after, "_p") else after

    def _put(self, new_el):
        self.el.addnext(new_el)
        self.el = new_el

    def para(self, runs, style="Normal", align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, keep_next=False, size=None, bullet=False):
        p = doc.add_paragraph(style=style)
        if bullet:
            old = p._p.pPr
            if old is not None:
                p._p.remove(old)
            p._p.insert(0, copy.deepcopy(list_ppr))
        p.alignment = align
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.keep_with_next = keep_next
        for r in ([runs] if isinstance(runs, (str, tuple)) else runs):
            text, fmt = (r, "") if isinstance(r, str) else r
            run = p.add_run(text)
            run.bold = "b" in fmt
            run.italic = "i" in fmt
            run.font.superscript = "^" in fmt
            run.font.color.rgb = RGBColor(0, 0, 0)
            if size:
                run.font.size = Pt(size)
        self._put(p._p)
        return p

    def label(self, text):
        return self.para([(text, "b")], align=WD_ALIGN_PARAGRAPH.LEFT, space_after=2, keep_next=True)

    def caption(self, num, text, above=False):
        return self.para([(num, "b"), " " + text], size=10, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4 if above else 10, keep_next=above)

    def figure(self, file, width_in):
        doc.add_picture(str(FIG / file), width=Inches(width_in))
        p = doc.paragraphs[-1]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(6)
        self._put(p._p)

    def table(self, rows, widths):
        t = doc.add_table(rows=len(rows), cols=len(rows[0]))
        t.autofit = False
        tblpr = t._tbl.tblPr
        tw = tblpr.find(W + "tblW")
        if tw is None:
            tw = tblpr.makeelement(W + "tblW", {})
            tblpr.append(tw)
        tw.set(W + "w", str(int(sum(widths) * 1440)))
        tw.set(W + "type", "dxa")
        for gc, wi in zip(t._tbl.tblGrid.findall(W + "gridCol"), widths):
            gc.set(W + "w", str(int(wi * 1440)))
        borders = tblpr.makeelement(W + "tblBorders", {})
        for side, sz in (("top", "8"), ("bottom", "8"), ("insideH", "2")):
            e = borders.makeelement(W + side, {W + "val": "single", W + "sz": sz, W + "space": "0", W + "color": "000000" if side != "insideH" else "BFBFBF"})
            borders.append(e)
        after = next((tblpr.find(W + t) for t in ("shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription") if tblpr.find(W + t) is not None), None)
        if after is not None:
            after.addprevious(borders)  # schema order: borders come before shading, layout, margins and look
        else:
            tblpr.append(borders)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                c = t.cell(i, j)
                c.width = Inches(widths[j])
                p = c.paragraphs[0]
                p.paragraph_format.space_after = Pt(1)
                run = p.add_run(str(val))
                run.font.size = Pt(9)
                run.bold = i == 0
                run.font.color.rgb = RGBColor(0, 0, 0)
            if i == 0:
                trpr = t.rows[0]._tr.get_or_add_trPr()
                trpr.append(trpr.makeelement(W + "tblHeader", {}))
        self._put(t._tbl)
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_after = Pt(4)
        self._put(spacer._p)


# ---------------------------------------------------------------- article information
TITLE = ("Multilingual first aid dataset: a source-cited procedure corpus with labelled emergency messages and "
         "safety test sets in English, Hindi, Hinglish and Marathi")
c = Cursor(heads["ARTICLE INFORMATION"])
c.label("Article title")
c.para(TITLE, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=8)
c.label("Authors")
c.para(["Atharva Hemade", ("a,*", "^"), ", Taneesha Badhe", ("a", "^"), ", Siddhi Karhekar", ("a", "^"), ", Soham Ghodake", ("a", "^")], align=WD_ALIGN_PARAGRAPH.LEFT, space_after=8)
c.label("Affiliations")
c.para([("a", "^"), "School of Computer Engineering and Technology, MIT World Peace University, Kothrud, Pune 411038, Maharashtra, India"], align=WD_ALIGN_PARAGRAPH.LEFT, space_after=8)
c.label("Corresponding author’s email address and Twitter handle")
c.para("[institutional email address of the corresponding author]", align=WD_ALIGN_PARAGRAPH.LEFT, space_after=8)
c.label("Keywords")
c.para("Emergency triage; Code-mixing; Low-resource languages; Negation detection; Clinical practice guidelines; Natural language processing", align=WD_ALIGN_PARAGRAPH.LEFT, space_after=8)
c.label("Abstract")
c.para(
    "Untrained bystanders are often the only help in the first minutes of an emergency, and in India they describe what they see in "
    "everyday, frequently code-mixed language. This article describes a dataset built to support first aid guidance in four languages: "
    "English, Hindi, Hinglish (romanised Hindi mixed with English) and Marathi. The procedure corpus contains five adult first aid "
    f"situations (unresponsiveness, heart attack, choking, bites and burns) as {S['n_steps']} ordered steps in {S['n_branches']} branches, "
    f"with {S['n_do_not']} do-not rules, {S['myths']} harmful home remedies and {S['questions']} clarifying questions. Every step cites one of "
    "five guidelines published between 2024 and 2026 (IFRC, AHA/American Red Cross, AHA basic life support, ILCOR and India’s National "
    f"Action Plan for Snakebite Envenoming), and all {S['loc_strings']} text strings are available in the four languages. Four word lists "
    f"({n(sum(v['terms'] for v in S['lex'].values()))} phrases with negation and uncertainty cues) map everyday phrasing to twelve structured "
    f"facts. The message corpus contains {n(S['train'] + S['dev'])} template-generated emergency descriptions (900 per language) labelled "
    "with situation, subtype, urgency and facts; a team-written safety suite of "
    f"{S['suite']} messages ({S['suite_em']} that must be treated as emergencies); a {S['probe']}-message probe set of short, misspelt, "
    f"code-mixed messages with silver labels; and {n(S['verifier'])} sentence pairs that pair each step with a safe rewording or a "
    "meaning-changing edit. Pictures and animations for key steps are included with licence records. All files are UTF-8 JSON or JSON "
    "Lines with a JSON Schema, and the scripts that generate the messages and the statistics are included. The data can be reused to "
    "train and evaluate emergency triage, situation classification, language identification and negation handling for Indian languages, "
    "to test whether a model can tell a safe paraphrase of a medical instruction from a dangerous one, and as a cited, structured first "
    "aid knowledge base.", space_after=8)

# ---------------------------------------------------------------- specifications table
t = next(tb for tb in doc.tables)
for sdt in list(t._tbl.iter(W + "sdt")):          # unwrap the Subject drop-down, keep its cell
    tc = sdt.find(W + "sdtContent").find(W + "tc")
    sdt.addprevious(tc)
    sdt.getparent().remove(sdt)
tw = t._tbl.tblPr.find(W + "tblW")
tw.set(W + "w", "9026")
grid = t._tbl.tblGrid.findall(W + "gridCol")
grid[0].set(W + "w", "1875")
grid[-1].set(W + "w", str(9026 - 1875))
for tr in t._tbl.findall(W + "tr"):
    tcs = tr.findall(W + "tc")
    tcs[-1].find(W + "tcPr/" + W + "tcW").set(W + "w", str(9026 - 1875))
SPEC = [
    ["Computer Sciences"],
    ["Natural language processing for multilingual first aid guidance: cited procedures and labelled emergency messages in four languages."],
    ["Table (JSON, JSON Lines), Image (WebP, SVG), Figure", "Raw: procedure steps written from guidelines; Processed: labelled and generated messages, sentence pairs"],
    ["Procedure steps were written by four team members from five first aid guidelines, each citing source and page, then translated into Hindi, "
     "Marathi and Hinglish. Messages were generated from hand-written templates with a Python script; the safety suite was written by the team; "
     "the probe set was drafted with an AI assistant and labelled by rule; verifier pairs were generated from the steps. Files were validated "
     "against a JSON Schema and automated tests."],
    ["Institution: MIT World Peace University", "City/Town/Region: Pune, Maharashtra", "Country: India",
     "Primary sources: first aid guidelines G1–G5 (IFRC 2025, AHA/Red Cross 2024, AHA 2025, ILCOR 2025, NAPSE 2024) [1–5]"],
    ["Repository name: GitHub (firstaid-assitant) [6]", "Data identification number: [DOI to be added after archiving the repository, e.g. on Zenodo or Mendeley Data]",
     "Direct URL to data: https://github.com/atharva-1910/firstaid-assitant",
     "Instructions for accessing these data: open access, no registration; data are in backend/content, backend/data and backend/tests."],
    ["None"],
]
for row, vals in zip(t.rows, SPEC):
    cell = row.cells[-1]
    for p in cell.paragraphs[1:]:
        p._p.getparent().remove(p._p)
    p0 = cell.paragraphs[0]
    for child in list(p0._p):
        if child.tag != W + "pPr":
            p0._p.remove(child)
    for k, v in enumerate(vals):
        p = p0 if k == 0 else cell.add_paragraph()
        run = p.add_run(v)
        run.font.color.rgb = RGBColor(0, 0, 0)
        run.italic = False
        run.underline = False

# ---------------------------------------------------------------- value of the data
c = Cursor(heads["VALUE OF THE DATA"])
for txt in [
    "To the authors’ knowledge, this is the first first aid dataset that stores procedures as ordered, branching steps with a guideline "
    "citation on every step, in English, Hindi, Hinglish and Marathi, rather than as unordered English question–answer pairs.",
    f"The {n(S['train'] + S['dev'])} labelled messages, the team-written safety suite and the probe set allow researchers to train and compare "
    "emergency triage and situation classifiers per language, including code-mixed Hinglish, and to measure how often an emergency is missed.",
    "The word lists with language-specific negation and uncertainty cues, together with the facts labelled on every message, support work on "
    "negation scope and fact extraction in Indian languages, where the negation cue often follows the verb.",
    f"The {n(S['verifier'])} step pairs, labelled as the same or a different instruction, provide a ready test of whether a paraphrase or "
    "entailment model can catch dangerous edits to medical text, such as a removed “do not” or a changed number.",
    "The cited, translated procedure records and harmful-remedy list can be reused as a knowledge base for first aid apps, chatbots and "
    "training materials, and the generation scripts let others extend the data to further languages or situations.",
]:
    c.para(txt, style="List Paragraph", bullet=True, space_after=4)

# ---------------------------------------------------------------- background
c = Cursor(heads["BACKGROUND"])
c.para("First aid guidance is published by international bodies as long documents in English [1–4], while the people who need it in India "
       "describe an emergency in everyday Hindi, Marathi or Hinglish and often follow harmful remedies such as tying a rope above a snakebite [5]. "
       "Existing first aid datasets are English question–answer lists without step order or sources, and code-mixed Hindi–English resources "
       "mostly cover social-media tasks [9,10]. The data were compiled to build and test an assistant that shows only verified, cited first "
       "aid steps and uses natural language processing solely to decide which steps to show and when to raise an alarm.")
c.para("This design required two kinds of data. The first is a structured, hand-checked procedure corpus, so that no step text is ever "
       "generated by a model. The second is a set of labelled messages and test sets in four languages to develop and evaluate language "
       "identification, fact extraction with negation handling, which clinical text processing treats as a core problem [7,8], and urgency "
       "classification. The procedure records follow a JSON Schema that rejects any step without a source, and the message sets were "
       "designed so that results can be reported per language.")

# ---------------------------------------------------------------- data description
c = Cursor(heads["DATA DESCRIPTION"])
c.para(f"The dataset [6] is stored in the repository’s backend folder as UTF-8 JSON and JSON Lines files (Table 1). The procedure corpus "
       f"and its supporting files are in backend/content; the message sets are in backend/data and backend/tests; pictures are in "
       f"frontend/public/steps.")
c.caption("Table 1.", "Files in the dataset.", above=True)
c.table([
    ["Folder / file", "Records", "Format", "Content"],
    ["content/situations/*.json (5 files)", f"{S['n_steps']} steps, {S['n_branches']} branches", "JSON", "Procedure records: unresponsive, heart_attack, choking, bites, burns"],
    ["content/lexicons/{en,hi,hinglish,mr}.json", f"{n(sum(v['terms'] for v in S['lex'].values()))} phrases", "JSON", "Phrases for each fact, negation and uncertainty cues, actions, age and time units"],
    ["content/myths.jsonl", f"{S['myths']}", "JSON Lines", "Harmful home remedies with reason, source and matching patterns"],
    ["content/questions.json", f"{S['questions']}", "JSON", "Clarifying questions with answer options and the facts each answer sets"],
    ["content/strings.json", "—", "JSON", "Disclaimer and handover-summary text in four languages"],
    ["content/schema/situation.schema.json", "—", "JSON Schema", "Required fields and allowed values of a procedure record"],
    ["data/queries/train.jsonl, dev.jsonl", f"{n(S['train'])}, {S['dev']}", "JSON Lines", "Template-generated messages with labels"],
    ["tests/safety_suite.jsonl", f"{S['suite']}", "JSON Lines", "Team-written must-pass messages"],
    ["data/queries/probe_labelled.jsonl", f"{S['probe']}", "JSON Lines", "Short, misspelt, code-mixed messages with silver labels"],
    ["data/verifier/adversarial.jsonl", f"{n(S['verifier'])}", "JSON Lines", "Step / candidate pairs labelled same or different"],
    ["data/queries/test.jsonl", "0", "JSON Lines", "Placeholder for a hand-written test set"],
    ["frontend/public/steps/", f"{S['images']} steps, {S['anims']} animations", "WebP, SVG", "Step pictures and animations with licence records"],
], [2.0, 1.15, 0.85, 2.25])

c.para(f"Each procedure record holds the situation name and recognition signs in four languages, the fact that selects a branch, and the "
       f"branches with their steps, do-not rules and urgency rules (Table 2). A step stores its text in four languages, its order and the next "
       f"step, which can depend on a fact (for example, breathing normally leads to the recovery position and not breathing to CPR), and its "
       f"source as a document code (G1–G5) and page.")
c.caption("Table 2.", "Fields of a procedure step (content/situations/*.json).", above=True)
c.table([
    ["Field", "Type", "Description / allowed values"],
    ["id, order", "Text, integer", "Step identifier (e.g. burns_fire_s2) and position in the branch"],
    ["text.en / .hi / .hinglish / .mr", "Text", "The instruction in each language"],
    ["next", "Text or rule", "Next step, or {on: fact, cases: {value: step}} for a branch point"],
    ["source.doc, source.page", "Code, integer", "G1–G5 or UNSOURCED; page in the source document (null if not yet filled)"],
    ["also_in", "List", "Supporting sources"],
    ["agreement", "Categorical", "agree, differ, single_source, unchecked"],
    ["evidence", "Categorical", "strong, weak, good_practice, unchecked"],
    ["verified, verify_note", "Boolean, text", "Whether the step has been checked against the source, and what to check"],
    ["image, animation", "Object", "File, author, licence, licence URL, source URL and alt text in four languages"],
    ["aid, check", "Object", "Timer, stopwatch, counter or time note; a Yes/No question routing to the matching step"],
], [1.85, 1.0, 3.4])

c.para(f"The message files share one record format (Table 3). Each template message carries a situation (six classes: five situations and "
       f"out_of_scope, which includes child and infant cases), a subtype, an urgency (emergency, clinic or home; empty for out_of_scope) and the "
       f"facts it states (slots). The {n(S['train'] + S['dev'])} template messages are balanced at 150 per class per language. The safety suite "
       f"records whether each message must be treated as an emergency; the verifier pairs record the kind of edit and the label.")
c.caption("Table 3.", "Fields of the message files.", above=True)
c.table([
    ["File", "Fields", "Example values"],
    ["train / dev", "id, lang, text, situation, subtype, urgency, slots, split, written_by", "hinglish, burns, electrical, emergency, {burn_cause: electrical}"],
    ["safety_suite", "id, lang, text, must_be_emergency, expect", "true, bites"],
    ["probe_labelled", "id, lang, text, situation, subtype, urgency, labelled_by", "bites, insect_sting, emergency"],
    ["adversarial", "premise, hypothesis, lang, kind, label, source", "number_changed, different, burns_fire_s2-en"],
], [1.15, 2.9, 2.2])

lens = S["e4"]
c.para(f"The {S['n_steps']} steps are distributed over branches as shown in Fig. 1; the unresponsive record is the longest (14 steps) because "
       f"it splits into a CPR path and a recovery-position path. The IFRC guideline (G1) is the main source of {S['prim']['G1']} steps "
       f"({pct(S['prim']['G1'], S['n_steps'])}), the AHA guidelines (G2, G3) of {S['prim']['G2'] + S['prim']['G3']}, and "
       f"{S['prim'].get('UNSOURCED', 0)} electrical-injury steps have no source yet (Fig. 2a). The {S['myths']} harmful remedies cite G1 ({S['myth_src'].get('G1', 0)}), "
       f"G5 ({S['myth_src'].get('G5', 0)}) and G2 ({S['myth_src'].get('G2', 0)}) (Fig. 2b).")
c.figure("steps.png", 6.2)
c.caption("Fig. 1.", "Number of steps (bars) and do-not rules (dots) in each branch of the procedure corpus.")
c.figure("sources.png", 6.3)
c.caption("Fig. 2.", "(a) Guideline cited by each step as main or supporting source; (b) sources of the harmful-remedy entries.")
u = S["urgency"]
tot = S["train"] + S["dev"]
c.para(f"Fig. 3 shows the subtypes and urgency labels of the template messages. Of the {n(tot)} messages, {n(u['emergency'])} "
       f"({pct(u['emergency'], tot)}) are emergencies, {u['clinic']} clinic, {u['home']} home, and {u['None']} have no urgency (out of scope). "
       f"Template messages average {lens['train (template)']['en']['mean_words']:.1f} words in English, {lens['train (template)']['hi']['mean_words']:.1f} in Hindi, "
       f"{lens['train (template)']['hinglish']['mean_words']:.1f} in Hinglish and {lens['train (template)']['mr']['mean_words']:.1f} in Marathi; safety-suite and probe messages "
       f"are shorter and use more distinct words per message (Fig. 4). The 720 English training messages use {lens['train (template)']['en']['vocabulary']} distinct words. "
       f"{pct(lens['train (template)']['hinglish']['share_code_mixed'], 1)[:-3]}% of Hinglish template messages and "
       f"{pct(lens['probe']['hinglish']['share_code_mixed'], 1)[:-3]}% of Hinglish probe messages contain both Hindi and English words "
       f"(mean Code-Mixing Index [9] {lens['train (template)']['hinglish']['cmi_mean']:.1f} and {lens['probe']['hinglish']['cmi_mean']:.1f}).")
c.figure("messages.png", 6.3)
c.caption("Fig. 3.", "(a) Template messages per subtype; (b) urgency labels (train + dev, n = 3,600).")
c.figure("language.png", 6.3)
c.caption("Fig. 4.", "(a) Average words per message and (b) distinct words in 24 messages, by message set and language.")
c.caption("Table 4.", "Messages per language in each message set.", above=True)
sl = S["suite_lang"]
vl = S["ver_lang"]
c.table([
    ["Set", "English", "Hindi", "Hinglish", "Marathi", "Total"],
    ["Template (train + dev)", "900", "900", "900", "900", n(tot)],
    ["Safety suite", str(sl["en"]), str(sl["hi"]), str(sl["hinglish"]), str(sl["mr"]), str(S["suite"])],
    ["Probe", "25", "25", "25", "25", str(S["probe"])],
    ["Verifier pairs", str(vl["en"]), str(vl["hi"]), str(vl["hinglish"]), str(vl["mr"]), n(S["verifier"])],
], [1.9, 0.85, 0.85, 0.85, 0.85, 0.85])
vk = S["ver_kind"]
c.para(f"Of the {n(S['verifier'])} verifier pairs, {S['ver_label']['same']} are labelled same (identity {vk['identity']}, punctuation "
       f"{vk['punctuation']}, polite form {vk['polite_form']}) and {S['ver_label']['different']} different (negation removed {vk['negation_removed']}, "
       f"negation added {vk['negation_added']}, antonym {vk['antonym']}, number changed {vk['number_changed']}, call to 112 dropped {vk['call_dropped']}) "
       f"(Fig. 5a). Page numbers are filled for {S['page_filled']} of {S['n_steps']} steps; agreement and evidence labels are unchecked and no step is "
       f"yet marked verified, and all five records have review status draft (Fig. 5b). Fig. 6 shows an excerpt of the English template messages and safety suite.")
c.figure("verifier_status.png", 6.3)
c.caption("Fig. 5.", "(a) Verifier pairs by kind of edit; (b) curation status of the procedure steps.")
c.figure("excerpt.png", 5.6)
c.caption("Fig. 6.", "Excerpt of data/queries/train.jsonl and tests/safety_suite.jsonl (English rows).")

# ---------------------------------------------------------------- methods
c = Cursor(heads["EXPERIMENTAL DESIGN, MATERIALS AND METHODS"])
c.para("Fig. 7 summarises how the files were produced.")
c.figure("workflow.png", 6.2)
c.caption("Fig. 7.", "Workflow from raw sources to the dataset files.")


def sub(head, text):
    c.para([(head, "b")], align=WD_ALIGN_PARAGRAPH.LEFT, space_after=2, keep_next=True)
    c.para(text)


sub("Source selection.", "Only first aid guidance published after 2020 by recognised bodies was used: the IFRC International First Aid, "
    "Resuscitation and Education Guidelines 2025 (G1) [1], the 2024 AHA and American Red Cross Guidelines for First Aid (G2) [2], the 2025 AHA "
    "adult basic life support guidelines (G3) [3], the ILCOR 2025 consensus on first aid science (G4) [4] and India’s National Action Plan for "
    "Prevention and Control of Snakebite Envenoming (G5) [5]. Five adult situations were selected: unresponsiveness, heart attack, choking, bites "
    "(snake, insect, scorpion, dog) and burns (fire or heat, chemical, electrical).")
sub("Procedure records.", "Each situation was assigned to one author, who read the relevant sections (for example IFRC Burns, p. 288), listed the "
    "recommended actions in order, and rewrote each as one short instruction beginning with a verb. Steps were first written as tables in a "
    "project specification with the source and page beside each step, then converted to JSON records following situation.schema.json. Branch "
    "points were added where the advice depends on a fact, and do-not rules, urgency rules and harmful remedies were added from the same "
    "sources. Supporting sources, agreement and evidence fields were initialised as unchecked, to be completed during verification.")
sub("Translation.", f"All {S['loc_strings']} strings were drafted in Hindi, Marathi and Hinglish and assigned to the author responsible for each "
    "language for line-by-line checking. Hinglish text is written in natural romanised spelling rather than transliterated from Hindi.")
sub("Word lists.", "For every structured fact (responsiveness, breathing, chest pain, choking signs, bite type, allergy signs, burn cause, burn "
    "area, power, age, time and actions taken), each language owner listed common phrasings and spelling variants, together with negation and "
    "uncertainty cues and the direction in which a cue applies (before the word in English, after the verb in Hindi, Hinglish and Marathi). "
    "Phrases missed on the probe set (for example “saans ruk gayi”, “छाती जड”) were added once and are covered by regression tests.")
sub("Template messages.", "backend/scripts/generate_queries.py fills hand-written templates per language and class with people (for example “my "
    "father”, “dadaji”), times (“10 minutes ago”) and wrappers (“please help”), assigning the template’s labels to each message. It produces "
    "150 messages per class per language, split 80/20 into train and dev with a fixed random seed. Labels come only from the templates.")
sub("Safety suite and probe set.", f"The safety suite was written by the authors in all four languages, covering each situation, harmful-remedy "
    f"mentions and non-emergencies such as a small burn or a fever ({S['suite_em']} must-be-emergency and {S['suite'] - S['suite_em']} other cases). The "
    "probe set was drafted with an AI assistant as 25 short, misspelt and code-mixed messages per language and labelled with situation and "
    "urgency following the project’s rules; these labels are marked as silver for checking by the authors.")
sub("Verifier pairs.", "backend/research/e7_verifier.py creates, from every step and do-not rule in each language, safe variants (identity, "
    "punctuation change, polite verb form) and dangerous variants (negation removed or added, number changed, call to 112 removed, antonym "
    "substitution), each recorded with its kind, label and source step.")
sub("Pictures.", "Five step pictures were taken from Wikimedia Commons under CC BY-SA 4.0 or CC0 and the remaining pictures and three animations "
    "were drawn by the authors and released under CC0. Pictures were resized to 500 px, placed on a white background and saved as WebP; author, "
    "licence, source URL and alt text in four languages are stored with each step.")
sub("Validation and statistics.", "Every procedure record is validated against situation.schema.json, and the repository’s automated tests check "
    "that every step has a source and every string exists in all four languages. The statistics and figures in this article were computed "
    "with docs/data_article/analyze_data.py using Python 3 and Matplotlib [14]; the Code-Mixing Index follows [9]. The annotation kit in "
    f"docs/annotation computes Cohen’s kappa [13] for future hand-written test sets. XNLI [11] and IndicXNLI [12] are referenced by the "
    "training notebooks but are not redistributed.")

# ---------------------------------------------------------------- limitations
c = Cursor(heads["LIMITATIONS"])
c.para(f"No procedure step has yet been verified against its source document ({S['verified']} of {S['n_steps']} marked verified), "
       f"{S['n_steps'] - S['page_filled']} steps still lack a page number, and two electrical-injury steps have no post-2020 source. The translations "
       "were machine-drafted and are still being checked by native speakers. The template messages repeat a small vocabulary and are longer than "
       "real messages, so they do not represent real-world language. The probe set was drafted with an AI assistant, has silver labels and was "
       "used once to extend the word lists. The hand-written test set (data/queries/test.jsonl) is empty. The procedures cover adults only.")

# ---------------------------------------------------------------- ethics, CRediT, acknowledgements, interests
c = Cursor(heads["ETHICS STATEMENT"])
c.para("The authors have read and follow the ethical requirements for publication in Data in Brief and confirm that the current work does not "
       "involve human subjects, animal experiments, or any data collected from social media platforms. All messages are invented examples and "
       "contain no personal data.")
credit_head = next(k for k in heads if k.startswith("CREDIT"))
c = Cursor(heads[credit_head])
c.para("Atharva Hemade: Conceptualization, Data curation (choking records, Hindi), Software, Writing – original draft. Taneesha Badhe: Data "
       "curation (unresponsive and heart attack records, English), Investigation, Writing – review & editing. Siddhi Karhekar: Data curation "
       "(bites records, Marathi), Validation, Writing – review & editing. Soham Ghodake: Data curation (burns records, Hinglish), Formal "
       "analysis, Writing – review & editing.")
c = Cursor(heads["ACKNOWLEDGEMENTS"])
c.para("The authors thank the Wikimedia Commons contributors BruceBlaus, Mrmw, Trakotako and Evolution and evolvability, whose openly licensed "
       "illustrations are included. This research did not receive any specific grant from funding agencies in the public, commercial, or "
       "not-for-profit sectors.")
c = Cursor(heads["DECLARATION OF COMPETING INTERESTS"])
c.para("The authors declare that they have no known competing financial interests or personal relationships that could have appeared to "
       "influence the work reported in this paper.")

# ---------------------------------------------------------------- references
c = Cursor(heads["REFERENCES"])
for i, ref in enumerate([
    "International Federation of Red Cross and Red Crescent Societies, International First Aid, Resuscitation and Education Guidelines 2025, IFRC, Geneva, 2026. https://www.ifrc.org/media/78476",
    "E.K. Hewett Brumberg, M.J. Douma, K. Alibertis, et al., 2024 American Heart Association and American Red Cross guidelines for first aid, Circulation 150 (2024). https://doi.org/10.1161/CIR.0000000000001281",
    "American Heart Association, 2025 American Heart Association guidelines for cardiopulmonary resuscitation and emergency cardiovascular care, Part 7: Adult basic life support, 2025. https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/adult-basic-life-support",
    "International Liaison Committee on Resuscitation, 2025 International consensus on first aid science with treatment recommendations, 2025. https://www.ilcor.org/uploads/FA-2025-COSTR-Full-Chapter.pdf",
    "Ministry of Health and Family Welfare, Government of India, National Action Plan for Prevention and Control of Snakebite Envenoming (NAPSE), 2024. https://ncdc.mohfw.gov.in/wp-content/uploads/2024/07/NATIONAL-ACTION-PLAN-FOR-PREVENTION-AND-CONTROL-OF-SNAKEBITE-ENVENOMING-NAPSE.pdf",
    "A. Hemade, T. Badhe, S. Karhekar, S. Ghodake, Multilingual first aid assistant: procedure corpus, message sets and code [dataset], GitHub, 2026. https://github.com/atharva-1910/firstaid-assitant",
    "W.W. Chapman, W. Bridewell, P. Hanbury, G.F. Cooper, B.G. Buchanan, A simple algorithm for identifying negated findings and diseases in discharge summaries, J. Biomed. Inform. 34 (2001) 301–310. https://doi.org/10.1006/jbin.2001.1029",
    "H. Harkema, J.N. Dowling, T. Thornblade, W.W. Chapman, ConText: An algorithm for determining negation, experiencer, and temporal status from clinical reports, J. Biomed. Inform. 42 (2009) 839–851. https://doi.org/10.1016/j.jbi.2009.05.002",
    "A. Das, B. Gambäck, Identifying languages at the word level in code-mixed Indian social media text, in: Proc. 11th Int. Conf. Natural Language Processing (ICON), Goa, India, 2014, pp. 378–387. https://aclanthology.org/W14-5152",
    "B.S. Harish, R.K. Rangan, A comprehensive survey on Indian regional language processing, SN Appl. Sci. 2 (2020) 1204. https://doi.org/10.1007/s42452-020-2983-x",
    "A. Conneau, R. Rinott, G. Lample, A. Williams, S. Bowman, H. Schwenk, V. Stoyanov, XNLI: Evaluating cross-lingual sentence representations, in: Proc. 2018 Conf. Empirical Methods in Natural Language Processing, 2018, pp. 2475–2485. https://doi.org/10.18653/v1/D18-1269",
    "D. Aggarwal, V. Gupta, A. Kunchukuttan, IndicXNLI: Evaluating multilingual inference for Indian languages, in: Proc. 2022 Conf. Empirical Methods in Natural Language Processing, 2022, pp. 10994–11006. https://doi.org/10.18653/v1/2022.emnlp-main.755",
    "J. Cohen, A coefficient of agreement for nominal scales, Educ. Psychol. Meas. 20 (1960) 37–46. https://doi.org/10.1177/001316446002000104",
    "J.D. Hunter, Matplotlib: A 2D graphics environment, Comput. Sci. Eng. 9 (2007) 90–95. https://doi.org/10.1109/MCSE.2007.55",
], start=1):
    c.para(f"[{i}] {ref}", align=WD_ALIGN_PARAGRAPH.LEFT, space_after=3, size=10)

doc.core_properties.title = TITLE
doc.core_properties.author = "Atharva Hemade, Taneesha Badhe, Siddhi Karhekar, Soham Ghodake"
doc.save(OUT)
print("wrote", OUT)
