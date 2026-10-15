"""Section 8.2: the safety rules floor. Always on, in both model modes.

The rules run on the facts after negation handling. A model may raise urgency but can
never lower it below what these rules return. Rules marked [VERIFY] in the spec are
implemented as written and listed in docs/VERIFY.md for the situation owners.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .urgency import max_urgency


@dataclass
class RuleHit:
    rule: str
    urgency: str
    triggers: list[tuple[str, str]]  # (slot or "flag", value) pairs that fired the rule
    situation: str | None = None


@dataclass
class RuleResult:
    urgency: str = "home"
    forced_situation: str | None = None
    hits: list[RuleHit] = field(default_factory=list)
    child: bool = False
    ask_slots: list[str] = field(default_factory=list)

    @property
    def triggers(self) -> list[tuple[str, str]]:
        out = []
        for h in self.hits:
            if h.urgency == "emergency":
                out.extend(h.triggers)
        return out


def _bites_context(slots: dict, flags: set, sits: dict) -> bool:
    return bool(slots.get("bite_type")) or "bite_word" in flags or "sting_word" in flags or sits.get("bites", 0) > 0


def evaluate(slots: dict, flags: set, sits: dict | None = None, uncertain: set | None = None) -> RuleResult:
    sits = sits or {}
    uncertain = uncertain or set()
    r = RuleResult()
    hits = r.hits

    responsive = slots.get("responsive")
    breathing = slots.get("breathing")
    choking_ctx = "choking_ctx" in flags or bool(slots.get("choking_signs"))

    # Unresponsive, or breathing absent / abnormal / gasping -> emergency, situation = unresponsive.
    if responsive == "no":
        hits.append(RuleHit("unresponsive", "emergency", [("responsive", "no")], "unresponsive"))
    elif "responsive_unsure" in flags:
        hits.append(RuleHit("unresponsive_unsure", "emergency", [("flag", "responsive_unsure")], "unresponsive"))
    if breathing in ("absent", "abnormal"):
        switch = responsive != "yes" and not (choking_ctx and responsive != "no")
        hits.append(RuleHit("breathing", "emergency", [("breathing", breathing)], "unresponsive" if switch else None))
    if "breathing_unsure" in flags and responsive == "no":
        hits.append(RuleHit("breathing_unsure", "emergency", [("flag", "breathing_unsure")], "unresponsive"))

    # Chest pain or pressure, or a stated heart attack.
    if slots.get("chest_pain") == "yes":
        hits.append(RuleHit("chest_pain", "emergency", [("chest_pain", "yes")], "heart_attack"))
    if "stated_heart_attack" in flags:
        hits.append(RuleHit("stated_heart_attack", "emergency", [("flag", "stated_heart_attack")], "heart_attack"))

    # Choking with weak cough, no sound, or cannot breathe.
    if slots.get("choking_signs") == "weak_or_silent":
        hits.append(RuleHit("choking_severe", "emergency", [("choking_signs", "weak_or_silent")], "choking"))

    # Bites and stings.
    bites = _bites_context(slots, flags, sits)
    bite_type = slots.get("bite_type")
    if bite_type == "snake":
        hits.append(RuleHit("snakebite", "emergency", [("bite_type", "snake")]))
    elif bites and not bite_type and ("bite_word" in flags or "bite_unsure" in flags):
        hits.append(RuleHit("unknown_bite", "emergency", [("flag", "bite_word")]))
    if bites and (slots.get("allergy_signs") == "yes" or "distress" in flags):
        trig = [("allergy_signs", "yes")] if slots.get("allergy_signs") == "yes" else [("flag", "distress")]
        hits.append(RuleHit("severe_allergy", "emergency", trig))
    if bites and "many_stings" in flags:
        hits.append(RuleHit("many_stings", "emergency", [("flag", "many_stings")]))
    if bite_type == "scorpion":
        hits.append(RuleHit("scorpion", "clinic", [("bite_type", "scorpion")]))  # [VERIFY]
    if bite_type in ("dog", "other_mammal"):
        if "severe_bite" in flags or "face_or_neck" in flags:
            trig = [("flag", "severe_bite")] if "severe_bite" in flags else [("flag", "face_or_neck")]
            hits.append(RuleHit("dog_bite_severe", "emergency", trig))  # [VERIFY]
        else:
            hits.append(RuleHit("dog_bite", "clinic", [("bite_type", bite_type)]))  # [VERIFY]

    # Burns.
    cause = slots.get("burn_cause")
    area = slots.get("burn_area")
    burns = bool(cause) or sits.get("burns", 0) > 0
    if cause == "electrical":
        hits.append(RuleHit("electrical", "emergency", [("burn_cause", "electrical")]))
    if cause == "chemical_acid" and (area in ("eyes_or_face", "large") or "acid_attack" in flags):
        trig = [("flag", "acid_attack")] if "acid_attack" in flags else [("burn_area", area)]
        hits.append(RuleHit("chemical_serious", "emergency", trig + [("burn_cause", "chemical_acid")]))  # [VERIFY]
    if burns and cause in (None, "fire_heat", "hot_liquid_steam"):
        if area in ("large", "eyes_or_face", "sensitive_area"):
            hits.append(RuleHit("thermal_serious", "emergency", [("burn_area", area)]))  # [VERIFY thresholds]
        elif "distress" in flags:
            hits.append(RuleHit("thermal_breathing", "emergency", [("flag", "distress")]))

    # Child or infant mentioned.
    if slots.get("age_group") in ("child", "infant"):
        r.child = True
        hits.append(RuleHit("child", "emergency", [("age_group", slots["age_group"])]))

    # Uncertain safety facts: ask about them before showing steps.
    for slot, flag in (("responsive", "responsive_unsure"), ("breathing", "breathing_unsure"), ("power_off", "power_unsure")):
        if slot in uncertain and slots.get(slot) is None and flag not in flags:
            r.ask_slots.append(slot)

    r.urgency = max_urgency("home", *[h.urgency for h in hits])
    # Situation forced by the rules. A person who becomes unresponsive always switches to unresponsive.
    for preferred in ("unresponsive", "heart_attack", "choking"):
        if any(h.situation == preferred for h in hits):
            r.forced_situation = preferred
            break
    return r
