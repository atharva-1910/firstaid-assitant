"""Loads and validates everything under backend/content/. All first aid text comes from here."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from .config import CONTENT_DIR, SITUATIONS


def _read_json(path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def schema() -> dict:
    return _read_json(CONTENT_DIR / "schema" / "situation.schema.json")


def validate_record(record: dict) -> list[str]:
    """Returns a list of validation errors (empty when the record is valid)."""
    import jsonschema

    validator = jsonschema.Draft202012Validator(schema())
    errors = [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in validator.iter_errors(record)]
    # Cross-reference checks the schema cannot express.
    for bkey, branch in record.get("branches", {}).items():
        ids = {s["id"] for s in branch.get("steps", [])}
        for s in branch.get("steps", []):
            nxt = s.get("next")
            targets = [nxt] if isinstance(nxt, str) else (list(nxt["cases"].values()) + [nxt["default"]] if isinstance(nxt, dict) else [])
            for t in targets:
                if t not in ids:
                    errors.append(f"branches/{bkey}/{s['id']}: next '{t}' does not exist")
        for d in branch.get("do_not", []):
            if d.get("step") and d["step"] not in ids:
                errors.append(f"branches/{bkey}/do_not: step '{d['step']}' does not exist")
    for target in (record.get("branch_map") or {}).values():
        if target not in record.get("branches", {}):
            errors.append(f"branch_map: '{target}' is not a branch")
    return errors


@lru_cache(maxsize=1)
def situations() -> dict[str, dict]:
    out = {}
    for sid in SITUATIONS:
        rec = _read_json(CONTENT_DIR / "situations" / f"{sid}.json")
        errs = validate_record(rec)
        if errs:
            raise ValueError(f"Invalid situation record {sid}: {errs[:5]}")
        out[sid] = rec
    return out


@lru_cache(maxsize=1)
def questions() -> dict[str, dict]:
    data = _read_json(CONTENT_DIR / "questions.json")
    return {q["id"]: q for q in data["questions"]}


@lru_cache(maxsize=1)
def myths() -> list[dict]:
    lines = (CONTENT_DIR / "myths.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines if l.strip()]


@lru_cache(maxsize=1)
def strings() -> dict:
    return _read_json(CONTENT_DIR / "strings.json")


@lru_cache(maxsize=8)
def raw_lexicon(lang: str) -> dict:
    return _read_json(CONTENT_DIR / "lexicons" / f"{lang}.json")


def localized(value: dict | None, lang: str) -> tuple[str, bool]:
    """Returns (text, translation_pending). Never machine-translates: missing text falls back to English."""
    if not value:
        return "", False
    text = (value.get(lang) or "").strip()
    if text:
        return text, False
    en = value.get("en", "")
    return en, lang != "en" and bool(en.strip())


def all_step_texts() -> set[str]:
    """Every step text in every language, for the 'no invented text' test."""
    texts: set[str] = set()
    for rec in situations().values():
        for branch in rec["branches"].values():
            for s in branch["steps"]:
                texts.update(v for v in s["text"].values() if v)
    return texts
