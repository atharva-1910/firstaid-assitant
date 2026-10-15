from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent
CONTENT_DIR = BACKEND_DIR / "content"


def _load_dotenv() -> None:
    """Tiny .env reader so the app has no extra dependency for it."""
    for candidate in (BACKEND_DIR / ".env", REPO_DIR / ".env"):
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

MODEL_MODE = os.environ.get("MODEL_MODE", "stub").lower()
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
REPHRASE_ENABLED = os.environ.get("REPHRASE_ENABLED", "false").lower() == "true"
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", str(2 * 60 * 60)))
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]

# Real-model locations (used only when MODEL_MODE=real)
TRIAGE_MODEL_PATH = os.environ.get("TRIAGE_MODEL_PATH", str(REPO_DIR / "training" / "out" / "indicbert_triage"))
SITUATION_MODEL_NAME = os.environ.get("SITUATION_MODEL_NAME", "BAAI/bge-m3")
VERIFIER_MODEL_PATH = os.environ.get("VERIFIER_MODEL_PATH", str(REPO_DIR / "training" / "out" / "mmbert_verifier"))
GEMMA_MODEL = os.environ.get("GEMMA_MODEL", "gemma3:4b")

LANGS = ("en", "hi", "hinglish", "mr")
SITUATIONS = ("unresponsive", "heart_attack", "choking", "bites", "burns")

# F2 thresholds (Section 8.4)
CONFIDENCE_THRESHOLD = 0.75
TOP_TWO_GAP = 0.15
MAX_QUESTIONS_IN_ROW = 2
