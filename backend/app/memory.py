"""Feature F2 (part 2): conversation memory (owner: Atharva Hemade).

An in-process store keyed by session_id that expires after 2 hours. Each message
updates the slots: a newer, certain value replaces an older or uncertain one; an
"unknown" or uncertain mention never overwrites a known fact.
"""
from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

from .config import SESSION_TTL_SECONDS
from .extract import SAFETY_SLOTS, Extraction


@dataclass
class Session:
    id: str
    created: float = field(default_factory=time.time)
    touched: float = field(default_factory=time.time)
    lang: str = "en"
    slots: dict = field(default_factory=dict)
    uncertain: set = field(default_factory=set)
    flags: set = field(default_factory=set)
    sits: dict = field(default_factory=dict)
    actions: list = field(default_factory=list)
    texts: list = field(default_factory=list)
    text_langs: list = field(default_factory=list)
    last_text: str = ""
    last_prediction: list = field(default_factory=list)  # classifier output for the last informative message
    answers: dict = field(default_factory=dict)  # question id -> option id
    asked: list = field(default_factory=list)  # question ids, in order
    questions_in_row: int = 0
    emergency_shown_for: set = field(default_factory=set)
    harmful_shown: set = field(default_factory=set)
    harmful_reported: list = field(default_factory=list)
    situation: str | None = None
    previous_situation: str | None = None
    fallback: bool = False

    def apply_extraction(self, ext: Extraction, text: str) -> None:
        self.texts.append(text)
        self.text_langs.append(ext.lang)
        self.last_text = text
        for slot, value in ext.slots.items():
            if slot == "time_since":
                self.slots[slot] = value
                continue
            self.slots[slot] = value  # newer certain value wins
            self.uncertain.discard(slot)
        for slot in ext.uncertain:
            if slot not in self.slots:
                self.uncertain.add(slot)
        # A new definite answer about responsiveness or breathing resets the "not sure" flags.
        for slot, flag in (("responsive", "responsive_unsure"), ("breathing", "breathing_unsure"), ("power_off", "power_unsure")):
            if slot in ext.slots:
                self.flags.discard(flag)
        self.flags.update(ext.flags)
        for s, w in ext.sits.items():
            self.sits[s] = self.sits.get(s, 0.0) + w
        for a in ext.actions:
            if a not in self.actions:
                self.actions.append(a)

    def apply_answer(self, question: dict, option: dict) -> None:
        self.answers[question["id"]] = option["id"]
        for slot, value in option.get("set", {}).items():
            self.slots[slot] = value
            self.uncertain.discard(slot)
        for flag in option.get("flags", []):
            self.flags.add(flag)
        for slot in SAFETY_SLOTS:
            if slot in option.get("set", {}):
                self.flags.discard({"responsive": "responsive_unsure", "breathing": "breathing_unsure", "power_off": "power_unsure"}[slot])


class SessionStore:
    def __init__(self, ttl: int = SESSION_TTL_SECONDS) -> None:
        self.ttl = ttl
        self._data: dict[str, Session] = {}
        self._lock = threading.Lock()

    def _expire(self) -> None:
        now = time.time()
        for sid in [k for k, s in self._data.items() if now - s.touched > self.ttl]:
            del self._data[sid]

    def get(self, session_id: str | None) -> Session | None:
        with self._lock:
            self._expire()
            s = self._data.get(session_id or "")
            if s:
                s.touched = time.time()
            return s

    def get_or_create(self, session_id: str | None) -> Session:
        s = self.get(session_id)
        if s:
            return s
        with self._lock:
            s = Session(id=uuid.uuid4().hex)  # unknown or expired ids start a fresh session
            self._data[s.id] = s
            return s

    def clear(self) -> None:
        with self._lock:
            self._data.clear()


store = SessionStore()
