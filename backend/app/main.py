"""FastAPI app and routes (Section 13.2). Nothing here calls an external API at runtime."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import config, content, pipeline, summary
from .memory import store
from .models import MODEL_NAMES

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Fails fast if any content file is invalid.
    content.situations()
    content.questions()
    content.myths()
    yield


app = FastAPI(title="Multilingual First Aid Assistant", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

UiLang = Literal["auto", "en", "hi", "hinglish", "mr"]


class AnalyzeRequest(BaseModel):
    session_id: str | None = None
    text: str = Field(min_length=1, max_length=2000)
    ui_lang: UiLang = "auto"


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer_id: str
    ui_lang: UiLang = "auto"


class SummaryRequest(BaseModel):
    session_id: str
    ui_lang: UiLang = "auto"
    completed_steps: int = Field(default=0, ge=0, le=100)


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    return pipeline.analyze(req.session_id, req.text, req.ui_lang)


@app.post("/api/answer")
def answer(req: AnswerRequest) -> dict:
    try:
        return pipeline.answer(req.session_id, req.question_id, req.answer_id, req.ui_lang)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found or expired. Please start again.")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/situations/{sid}")
def situation(sid: str, lang: str = "en", branch: str | None = None) -> dict:
    try:
        return pipeline.situation_view(sid, lang, branch)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unknown situation or branch")


@app.post("/api/summary")
def handover(req: SummaryRequest) -> dict:
    sess = store.get(req.session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    lang = req.ui_lang if req.ui_lang in config.LANGS else sess.lang
    out = summary.build(sess, lang, req.completed_steps)
    return {"session_id": sess.id, "display_lang": lang, "next_screen": "summary", **out}


@app.get("/api/health")
def health() -> dict:
    recs = content.situations()
    return {
        "status": "ok",
        "model_mode": config.MODEL_MODE,
        "versions": {
            "app": app.version,
            "models": MODEL_NAMES.get(config.MODEL_MODE, {}),
            "content": {sid: r["review_status"] for sid, r in recs.items()},
        },
    }


# Serve the built frontend (frontend/dist) from the same server when it exists, so a
# demo runs with one process: `npm run build` once, then `uvicorn app.main:app`.
_DIST = config.REPO_DIR / "frontend" / "dist"
if _DIST.exists():
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        target = (_DIST / path).resolve()
        if path and target.is_file() and _DIST.resolve() in target.parents:
            return FileResponse(target)
        return FileResponse(_DIST / "index.html")
