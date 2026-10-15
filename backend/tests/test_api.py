"""API shape (Section 13.2)."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

RESPONSE_KEYS = {
    "session_id", "detected_lang", "display_lang", "next_screen", "urgency", "situation", "child_or_infant",
    "out_of_scope", "clarifying_question", "explanation", "harmful_action", "slots", "steps", "do_not", "disclaimer",
}
SCREENS = {"question", "emergency", "steps", "harmful_warning", "child", "out_of_scope", "summary"}


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["model_mode"] in ("stub", "real")
    assert set(body["versions"]["content"]) == {"unresponsive", "heart_attack", "choking", "bites", "burns"}


def test_analyze_shape():
    r = client.post("/api/analyze", json={"session_id": None, "text": "papa gir gaye, saans nahi le rahe", "ui_lang": "auto"})
    assert r.status_code == 200
    body = r.json()
    assert RESPONSE_KEYS <= set(body)
    assert body["next_screen"] in SCREENS
    assert body["detected_lang"] == "hinglish"
    assert body["urgency"] == "emergency"
    assert body["situation"]["id"] == "unresponsive" and body["situation"]["branch"] == "path_a"
    step = body["steps"][0]
    assert {"id", "order", "text", "source", "agreement", "evidence", "translation_pending"} <= set(step)
    assert {"doc", "page"} <= set(step["source"])


def test_answer_flow_and_summary():
    r = client.post("/api/analyze", json={"text": "something bit him on the leg 20 minutes ago"}).json()
    q = r["clarifying_question"]
    assert q and q["id"] == "q_bite_type"
    r2 = client.post("/api/answer", json={"session_id": r["session_id"], "question_id": q["id"], "answer_id": "snake"})
    assert r2.status_code == 200 and RESPONSE_KEYS <= set(r2.json())
    s = client.post("/api/summary", json={"session_id": r["session_id"], "completed_steps": 3})
    assert s.status_code == 200
    lines = s.json()["lines"]
    assert 1 <= len(lines) <= 5
    assert "snake" in lines[0].lower() and "20 minutes" in lines[0]


def test_answer_unknown_session():
    r = client.post("/api/answer", json={"session_id": "nope", "question_id": "q_age", "answer_id": "adult"})
    assert r.status_code == 404


def test_answer_bad_option():
    sid = client.post("/api/analyze", json={"text": "burn"}).json()["session_id"]
    r = client.post("/api/answer", json={"session_id": sid, "question_id": "q_burn_cause", "answer_id": "banana"})
    assert r.status_code == 422


def test_situation_endpoint():
    r = client.get("/api/situations/bites", params={"lang": "mr", "branch": "snake"})
    assert r.status_code == 200
    body = r.json()
    assert body["branch"] == "snake" and body["steps"][0]["id"] == "bite_snake_s1"
    assert body["steps"][0]["translation_pending"] is False
    assert body["steps"][0]["text"].startswith("112 वर कॉल करा")
    cpr = client.get("/api/situations/unresponsive", params={"branch": "path_a"}).json()
    assert cpr["branch"] == "path_a" and cpr["steps"][3]["id"] == "unr_a1"
    assert client.get("/api/situations/stroke").status_code == 404


def test_ui_lang_override():
    body = client.post("/api/analyze", json={"text": "he is unconscious", "ui_lang": "hi"}).json()
    assert body["display_lang"] == "hi"


def test_empty_text_rejected():
    assert client.post("/api/analyze", json={"text": ""}).status_code == 422
