import json
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from app.memory import store  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_sessions():
    store.clear()
    yield
    store.clear()


def load_suite():
    lines = (BACKEND / "tests" / "safety_suite.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines if l.strip()]
