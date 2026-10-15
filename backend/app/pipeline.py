"""Orchestrates the runtime workflow of Section 7.1 for one message or one answer.

[1] normalise -> [2] language id -> [3] F1 extraction + F3 negation -> [4] safety layer
-> [5] situation + F2 clarifying question -> [6] verified steps -> [7] screens -> [8] summary
"""
from __future__ import annotations

from . import clarify, content, safety_rules
from .config import LANGS, MAX_QUESTIONS_IN_ROW, SITUATIONS
from .explain import explain
from .extract import extract
from .memory import Session, store
from .models import registry
from .urgency import max_urgency


# ---------------------------------------------------------------- steps

def branch_key(record: dict, slots: dict) -> str | None:
    if not record.get("branch_on"):
        return "default"
    value = slots.get(record["branch_on"]) or "unknown"
    return (record.get("branch_map") or {}).get(value)


def path_label(record: dict, slots: dict) -> str | None:
    if record.get("path_on") == "breathing":
        return "path_b" if slots.get("breathing") == "normal" else "path_a"
    return None


def linearize(branch: dict, slots: dict) -> list[dict]:
    steps = branch["steps"]
    by_id = {s["id"]: s for s in steps}
    order: list[dict] = []
    current = steps[0]["id"] if steps else None
    seen: set[str] = set()
    while current and current not in seen:
        seen.add(current)
        s = by_id[current]
        order.append(s)
        nxt = s.get("next")
        if isinstance(nxt, dict):
            current = nxt["cases"].get(slots.get(nxt["on"]) or "", nxt["default"])
        else:
            current = nxt
    return order


def _branch_urgency(branch: dict, slots: dict, flags: set) -> str | None:
    for rule in branch.get("urgency_rules", []):
        cond = rule["if"]
        ok = True
        for k, v in cond.items():
            if k == "flag":
                ok = ok and v in flags
            else:
                ok = ok and slots.get(k) == v
        if ok:
            return rule["urgency"]
    return None


def render_steps(record: dict, branch: dict, slots: dict, lang: str) -> list[dict]:
    models = registry()
    rephraser, verifier = models.get("rephraser"), models["verifier"]
    out = []
    do_nots = branch.get("do_not", [])
    path = linearize(branch, slots)
    for n, s in enumerate(path, start=1):
        text, pending = content.localized(s["text"], lang)
        rephrased = False
        if rephraser is not None and text:
            cand = rephraser.rephrase(text, lang, record)
            if cand and verifier.entails(text, cand, lang) and verifier.entails(cand, text, lang):
                text, rephrased = cand, True
        step_dn = []
        for d in do_nots:
            if d.get("step") == s["id"]:
                t, p1 = content.localized(d["text"], lang)
                r, p2 = content.localized(d.get("reason"), lang)
                step_dn.append({"text": t, "reason": r, "translation_pending": p1 or p2})
        out.append({
            "id": s["id"],
            "order": n,
            "text": text,
            "translation_pending": pending,
            "rephrased": rephrased,
            "source": {"doc": s["source"]["doc"], "page": s["source"].get("page")},
            "also_in": s.get("also_in", []),
            "agreement": s["agreement"],
            "evidence": s["evidence"],
            "verified": s["verified"],
            "verify_note": s.get("verify_note"),
            "cpr_rhythm": bool(s.get("cpr_rhythm")),
            "link": s.get("link"),
            "do_not": step_dn,
        })
    return out


def render_do_not(branch: dict, lang: str) -> list[dict]:
    out = []
    for d in branch.get("do_not", []):
        t, p1 = content.localized(d["text"], lang)
        r, p2 = content.localized(d.get("reason"), lang)
        out.append({"text": t, "reason": r, "translation_pending": p1 or p2, "step": d.get("step")})
    return out


# ---------------------------------------------------------------- questions

def render_question(qid: str, lang: str, reason: str) -> dict:
    q = content.questions()[qid]
    text, pending = content.localized(q["text"], lang)
    opts = []
    for o in q["options"]:
        label, p = content.localized(o["label"], lang)
        opts.append({"id": o["id"], "label": label, "translation_pending": p})
    return {"id": qid, "text": text, "translation_pending": pending, "options": opts, "safety": reason.startswith("safety")}


# ---------------------------------------------------------------- main entry points

def analyze(session_id: str | None, text: str, ui_lang: str = "auto") -> dict:
    sess = store.get_or_create(session_id)
    models = registry()
    lang = models["langid"].detect(text)["lang"]
    sess.lang = lang
    ext = extract(text, lang)
    sess.apply_extraction(ext, text)
    joined = " . ".join(sess.texts)
    sess.last_prediction = models["situation"].predict(joined, lang)
    sess.questions_in_row = 0
    return decide(sess, ui_lang, latest_text=text)


def answer(session_id: str, question_id: str, option_id: str, ui_lang: str = "auto") -> dict:
    sess = store.get(session_id)
    if sess is None:
        raise KeyError("session not found or expired")
    q = content.questions().get(question_id)
    if q is None:
        raise ValueError(f"unknown question {question_id}")
    opt = next((o for o in q["options"] if o["id"] == option_id), None)
    if opt is None:
        raise ValueError(f"unknown option {option_id} for {question_id}")
    sess.apply_answer(q, opt)
    if question_id not in sess.asked:
        sess.asked.append(question_id)
    return decide(sess, ui_lang, latest_text="")


def decide(sess: Session, ui_lang: str, latest_text: str) -> dict:
    models = registry()
    slots, flags = sess.slots, sess.flags
    lang = sess.lang
    display = ui_lang if ui_lang in LANGS else lang

    # [4] Safety rules floor.
    rules = safety_rules.evaluate(slots, flags, sess.sits, sess.uncertain)

    # [5] Situation identification, updated with the answers given so far.
    prediction = sess.last_prediction or [{"situation": s, "p": 1 / 6} for s in list(SITUATIONS) + ["out_of_scope"]]
    hyps = clarify.update_with_answers(clarify.hypotheses(prediction, slots), sess.answers)
    by_sit = clarify.situation_probs(hyps)
    forced = rules.forced_situation is not None
    situation = rules.forced_situation or by_sit[0]["situation"]
    confidence = 1.0 if forced else round(by_sit[0]["p"], 3)

    # Triage model (stub = rules) and harmful-action check on the newest message.
    candidates = {situation} | {s for s, w in sess.sits.items() if w > 0}
    triage = models["triage"].predict(latest_text, lang, {**slots, "_flags": sorted(flags), "_sits": sess.sits, "_situations": sorted(candidates)})
    harmful = None
    for h in triage.get("all_harmful") or []:
        action = h["myth"]["action"]["en"]
        if action not in sess.harmful_reported:
            sess.harmful_reported.append(action)
        if harmful is None and h["myth"]["id"] not in sess.harmful_shown:
            harmful = h

    # F2: clarifying question (at most 2 in a row).
    question = None
    reason = ""
    child = rules.child
    pregnant_choking = situation == "choking" and "pregnant_or_large" in flags
    if not child and not pregnant_choking:
        qid, reason = clarify.choose(
            hyps=hyps, slots=slots, flags=flags, asked=sess.asked, ask_slots=rules.ask_slots,
            situation=situation, forced=forced,
        )
        if qid and sess.questions_in_row >= MAX_QUESTIONS_IN_ROW:
            sess.fallback = True  # still unsure after 2 questions: show Call 112 and the most likely situation
            qid = None
        if qid:
            question = render_question(qid, display, reason)
            sess.asked.append(qid)
            sess.questions_in_row += 1
        elif reason == "no_useful_question" and not forced and by_sit[0]["p"] < 0.75:
            sess.fallback = True
    # While the situation itself is still unclear, show no steps yet; only the question.
    provisional = question is not None and reason == "information_gain" and not forced
    # Still unsure after the questions and nothing points to one situation: Call 112, no guessed steps.
    no_evidence_fallback = sess.fallback and question is None and not forced and by_sit[0]["p"] < 0.5
    out_of_scope = (situation == "out_of_scope" and question is None) or pregnant_choking or no_evidence_fallback
    if no_evidence_fallback:
        situation, confidence = "out_of_scope", round(by_sit[0]["p"], 3)

    # [6] Steps from the verified record.
    record = content.situations().get(situation)
    steps: list[dict] = []
    do_not: list[dict] = []
    branch_label = None
    branch_urg = None
    if record and not out_of_scope and not provisional:
        bkey = branch_key(record, slots)
        if bkey:
            branch = record["branches"][bkey]
            branch_label = path_label(record, slots) or bkey
            branch_urg = _branch_urgency(branch, slots, flags)
            steps = render_steps(record, branch, slots, display)
            do_not = render_do_not(branch, display)

    urgency = max_urgency(rules.urgency, triage.get("urgency"), branch_urg, "emergency" if sess.fallback else None)
    if child or pregnant_choking:
        urgency = "emergency"

    # Situation switch (e.g. a heart attack patient becomes unresponsive).
    situation_changed = None
    if situation in SITUATIONS and not provisional and not out_of_scope:
        if sess.situation and sess.situation != situation:
            situation_changed = {"from": sess.situation, "to": situation}
        sess.situation = situation

    # F4 explanation.
    triggers = rules.triggers or ([("sit", situation)] if situation in SITUATIONS else [])
    explanation = explain(sess.texts, sess.text_langs, urgency, triggers)
    fallback_note = None
    if sess.fallback and urgency == "emergency":
        fallback_note, _ = content.localized(content.strings()["fallback_explanation"], display)

    # Which screen comes first. The frontend walks emergency -> warning -> question -> steps.
    emergency_key = situation if situation in SITUATIONS else "_any"
    if child:
        next_screen = "child"
    elif urgency == "emergency" and emergency_key not in sess.emergency_shown_for:
        next_screen = "emergency"
        sess.emergency_shown_for.add(emergency_key)
    elif harmful is not None:
        next_screen = "harmful_warning"
    elif out_of_scope:
        next_screen = "out_of_scope"
    elif question is not None:
        next_screen = "question"
    else:
        next_screen = "steps"
    if harmful is not None:
        sess.harmful_shown.add(harmful["myth"]["id"])
    if question is None:
        sess.questions_in_row = 0

    harmful_out = None
    if harmful:
        a, p1 = content.localized(harmful["myth"]["action"], display)
        r, p2 = content.localized(harmful["myth"]["reason"], display)
        harmful_out = {"id": harmful["myth"]["id"], "action": a, "reason": r, "word": harmful["word"],
                       "source": harmful["myth"].get("source"), "translation_pending": p1 or p2}

    names = record["names"] if record else None
    name, name_pending = content.localized(names, display) if names else ("", False)
    oos_note = None
    if pregnant_choking:
        oos_note, _ = content.localized(content.situations()["choking"].get("out_of_scope_note"), display)
    disclaimer, _ = content.localized(content.strings()["disclaimer"], display)

    return {
        "session_id": sess.id,
        "detected_lang": lang,
        "display_lang": display,
        "next_screen": next_screen,
        "urgency": urgency,
        "situation": {"id": situation, "name": name, "branch": branch_label, "confidence": confidence} if situation in SITUATIONS else {"id": situation, "name": "", "branch": None, "confidence": confidence},
        "situation_changed": situation_changed,
        "provisional": provisional,
        "child_or_infant": child,
        "out_of_scope": out_of_scope,
        "out_of_scope_note": oos_note,
        "clarifying_question": question,
        "explanation": explanation,
        "fallback_note": fallback_note,
        "harmful_action": harmful_out,
        "slots": {k: v for k, v in slots.items()},
        "uncertain": sorted(sess.uncertain),
        "steps": steps,
        "do_not": do_not,
        "actions_taken": sess.actions,
        "disclaimer": disclaimer,
    }


def situation_view(sid: str, lang: str, branch: str | None) -> dict:
    record = content.situations().get(sid)
    if record is None:
        raise KeyError(sid)
    lang = lang if lang in LANGS else "en"
    slots: dict = {}
    if record.get("path_on") == "breathing":
        slots["breathing"] = "normal" if branch == "path_b" else "absent"
        bkey = "default"
    elif record.get("branch_on"):
        mapping = record.get("branch_map") or {}
        bkey = mapping.get(branch or "", branch) if branch else next(iter(record["branches"]))
        if bkey not in record["branches"]:
            raise KeyError(f"{sid}/{branch}")
        slots[record["branch_on"]] = next((k for k, v in mapping.items() if v == bkey), bkey)
    else:
        bkey = "default"
    b = record["branches"][bkey]
    name, _ = content.localized(record["names"], lang)
    return {
        "id": sid,
        "name": name,
        "owner": record["owner"],
        "review_status": record["review_status"],
        "branch": path_label(record, slots) or bkey,
        "branches": list(record["branches"]) if record.get("branch_on") else (list(record.get("paths", {})) or ["default"]),
        "recognition": [content.localized(r, lang)[0] for r in record["recognition"]],
        "urgency": _branch_urgency(b, slots, set()),
        "steps": render_steps(record, b, slots, lang),
        "do_not": render_do_not(b, lang),
        "source_differences": record.get("source_differences", []),
    }
