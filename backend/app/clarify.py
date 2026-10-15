"""Feature F2 (part 1): the smart clarifying question (owner: Atharva Hemade).

A question is needed when the top situation is below 0.75, the top two are within 0.15,
the subtype is unknown (bite type, burn cause), or a safety fact is unknown.
Safety questions always win; otherwise the question with the highest expected
information gain (entropy reduction over situation+subtype hypotheses) is asked.
"""
from __future__ import annotations

import math

from . import content
from .config import CONFIDENCE_THRESHOLD, TOP_TWO_GAP

SUBTYPES = {
    "bites": ("bite_type", ["snake", "insect_sting", "scorpion", "dog"]),
    "burns": ("burn_cause", ["fire_heat", "hot_liquid_steam", "chemical_acid", "electrical"]),
}
ANSWER_NOISE = 0.05  # chance that a person gives an answer the hypothesis does not predict
MISMATCH_FACTOR = 0.1  # posterior penalty when an answer contradicts a hypothesis
SAFETY_QUESTION = {"responsive": "q_responsive", "breathing": "q_breathing", "power_off": "q_power_off"}


def _norm_sub(slot_value: str | None) -> str | None:
    return "dog" if slot_value == "other_mammal" else slot_value


def hypotheses(prediction: list[dict], slots: dict) -> dict[str, float]:
    hyps: dict[str, float] = {}
    for item in prediction:
        sit, p = item["situation"], item["p"]
        if sit in SUBTYPES:
            slot, subs = SUBTYPES[sit]
            known = _norm_sub(slots.get(slot))
            if known in subs:
                hyps[f"{sit}:{known}"] = hyps.get(f"{sit}:{known}", 0.0) + p
            else:
                for s in subs:
                    hyps[f"{sit}:{s}"] = hyps.get(f"{sit}:{s}", 0.0) + p / len(subs)
        else:
            hyps[sit] = hyps.get(sit, 0.0) + p
    return _normalise(hyps)


def _normalise(h: dict[str, float]) -> dict[str, float]:
    total = sum(h.values()) or 1.0
    return {k: v / total for k, v in h.items()}


def expected_answer(question: dict, hyp: str) -> str | None:
    exp = question.get("expects", {})
    if hyp in exp:
        return exp[hyp]
    sit = hyp.split(":")[0]
    return exp.get(f"{sit}:*", exp.get(sit))


def update_with_answers(hyps: dict[str, float], answers: dict[str, str]) -> dict[str, float]:
    qs = content.questions()
    out = dict(hyps)
    for qid, ans in answers.items():
        q = qs.get(qid)
        if not q or ans == "not_sure":  # "not sure" carries no information about the situation
            continue
        for h in out:
            e = expected_answer(q, h)
            if e is not None and e != ans:
                out[h] *= MISMATCH_FACTOR
    return _normalise(out)


def entropy(p: dict[str, float]) -> float:
    return -sum(v * math.log2(v) for v in p.values() if v > 0)


def information_gain(question: dict, hyps: dict[str, float]) -> float:
    options = [o["id"] for o in question["options"]]
    n = len(options)

    def likelihood(a: str, h: str) -> float:
        e = expected_answer(question, h)
        if e is None:
            return 1.0 / n
        return 1.0 - ANSWER_NOISE if a == e else ANSWER_NOISE / max(1, n - 1)

    prior_h = entropy(hyps)
    expected_h = 0.0
    for a in options:
        joint = {h: p * likelihood(a, h) for h, p in hyps.items()}
        pa = sum(joint.values())
        if pa <= 0:
            continue
        post = {h: v / pa for h, v in joint.items()}
        expected_h += pa * entropy(post)
    return prior_h - expected_h


def top_two(hyps_by_situation: list[dict]) -> tuple[float, float]:
    ps = [d["p"] for d in hyps_by_situation] + [0.0, 0.0]
    return ps[0], ps[1]


def situation_probs(hyps: dict[str, float]) -> list[dict]:
    agg: dict[str, float] = {}
    for h, p in hyps.items():
        s = h.split(":")[0]
        agg[s] = agg.get(s, 0.0) + p
    return sorted(({"situation": s, "p": p} for s, p in agg.items()), key=lambda d: -d["p"])


def choose(
    *,
    hyps: dict[str, float],
    slots: dict,
    flags: set,
    asked: list[str],
    ask_slots: list[str],
    situation: str | None,
    forced: bool,
) -> tuple[str | None, str]:
    """Returns (question id or None, reason)."""
    qs = content.questions()
    not_asked = lambda qid: qid not in asked  # noqa: E731

    # 1. Uncertain safety facts (F3 found "maybe", "pata nahi", "कदाचित" ...).
    for slot in ask_slots:
        qid = SAFETY_QUESTION[slot]
        if not_asked(qid):
            return qid, "safety_uncertain"
    by_sit = situation_probs(hyps)
    p1, p2 = top_two(by_sit)
    sure = forced or p1 >= CONFIDENCE_THRESHOLD
    # 2. Safety facts that decide the steps.
    collapse_like = "collapse" in flags or (situation == "unresponsive" and sure)
    if collapse_like and slots.get("responsive") is None and slots.get("breathing") is None and "responsive_unsure" not in flags and not_asked("q_responsive"):
        return "q_responsive", "safety"
    if sure and situation == "unresponsive" and slots.get("responsive") != "yes" and slots.get("breathing") is None and "breathing_unsure" not in flags and not_asked("q_breathing"):
        return "q_breathing", "safety"
    if slots.get("burn_cause") == "electrical" and slots.get("power_off") is None and "power_unsure" not in flags and not_asked("q_power_off"):
        return "q_power_off", "safety"
    # 3. A critical fact for the steps.
    if sure and situation == "choking" and slots.get("choking_signs") is None and not_asked("q_can_cough"):
        return "q_can_cough", "critical"

    # 4. Low confidence, close top two, or unknown subtype -> information gain.
    subtype_unknown = False
    if situation in SUBTYPES:
        slot, _ = SUBTYPES[situation]
        unsure_flag = "bite_unsure" if situation == "bites" else None
        subtype_unknown = slots.get(slot) is None and (unsure_flag is None or unsure_flag not in flags)
    if forced and not subtype_unknown:
        return None, "forced"
    if p1 >= CONFIDENCE_THRESHOLD and (p1 - p2) >= TOP_TWO_GAP and not subtype_unknown:
        return None, "confident"

    pool = hyps
    if subtype_unknown and p1 >= CONFIDENCE_THRESHOLD:
        pool = _normalise({h: p for h, p in hyps.items() if h.startswith(situation + ":")})
    best, best_gain = None, 1e-6
    for qid, q in qs.items():
        if not q.get("use_in_gain") or not not_asked(qid):
            continue
        g = information_gain(q, pool)
        if g > best_gain:
            best, best_gain = qid, g
    if not best:
        return None, "no_useful_question"
    return best, ("subtype" if pool is not hyps else "information_gain")
