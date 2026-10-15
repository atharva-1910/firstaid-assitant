"""Handover summary for the ambulance crew, built only from what the user said (slots in memory)."""
from __future__ import annotations

from . import content
from .memory import Session


def _t(key: str, lang: str, **kw) -> tuple[str, bool]:
    text, pending = content.localized(content.strings()["summary"].get(key), lang)
    return (text.format(**kw) if kw else text), pending


def build(session: Session, lang: str, completed_steps: int = 0) -> dict:
    s = session.slots
    lines: list[tuple[str, bool]] = []
    head: list[tuple[str, bool]] = []
    if s.get("age_group") in ("adult", "child", "infant"):
        head.append(_t(f"age.{s['age_group']}", lang))

    sit = session.situation
    if sit == "bites":
        head.append(_t(f"event.bites.{s.get('bite_type') or 'unknown'}", lang))
    elif sit == "burns":
        head.append(_t(f"event.burns.{s.get('burn_cause') or 'unknown'}", lang))
        if s.get("burn_area"):
            head.append(_t(f"area.{s['burn_area']}", lang))
    elif sit in ("unresponsive", "heart_attack", "choking"):
        head.append(_t(f"event.{sit}", lang))
    if s.get("time_since"):
        head.append(_t("time", lang, time=s["time_since"]))
    if head:
        lines.append((" ".join(t for t, _ in head), any(p for _, p in head)))

    status: list[tuple[str, bool]] = []
    if s.get("responsive") in ("yes", "no"):
        status.append(_t(f"responsive.{s['responsive']}", lang))
    if s.get("breathing") in ("normal", "abnormal", "absent"):
        status.append(_t(f"breathing.{s['breathing']}", lang))
    if sit == "choking" and s.get("choking_signs") in ("weak_or_silent", "coughing_strongly"):
        status.append(_t(f"choking.{s['choking_signs']}", lang))
    if s.get("allergy_signs") == "yes" and sit == "bites":
        status.append(_t("allergy.yes", lang))
    if s.get("burn_cause") == "electrical" and s.get("power_off") == "no":
        status.append(_t("power.no", lang))
    if status:
        lines.append((" ".join(t for t, _ in status), any(p for _, p in status)))

    if session.actions:
        lines.append(_t("actions", lang, actions=", ".join(session.actions)))
    if session.harmful_reported:
        lines.append(_t("reported", lang, items="; ".join(session.harmful_reported)))
    if completed_steps:
        lines.append(_t("steps_done", lang, n=completed_steps))
    if not lines:
        lines.append(_t("nothing", lang))
    lines = lines[:5]
    return {
        "lines": [t for t, _ in lines],
        "translation_pending": any(p for _, p in lines),
        "text": "\n".join(t for t, _ in lines),
    }
