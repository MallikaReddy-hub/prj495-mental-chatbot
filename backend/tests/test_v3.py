import os
import sqlite3
import tempfile
from datetime import date, timedelta

DBFILE = f"{tempfile.mkdtemp()}/t4.db"
os.environ["DATABASE_URL"] = f"sqlite:///{DBFILE}"
os.environ["JWT_SECRET"] = "test-secret"
os.environ.pop("MODEL_SERVER_URL", None)
os.environ.pop("GEMINI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app import llm  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def signup(email):
    r = client.post("/auth/signup", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_mood_tracker_summary_and_streak():
    h = signup("m@b.com")
    today = date.today()
    for i, (mood, sleep) in enumerate([(2, 5), (3, 6), (4, 7), (4, 6), (5, 8), (1, 4)]):
        day = str(today - timedelta(days=5 - i))
        r = client.post("/journal", json={"mood": mood, "sleep_hours": sleep, "day": day,
                                          "tags": ["Exams", "exams", "family"]}, headers=h)
        assert r.status_code == 200
    assert r.json()["tags"] == ["exams", "family"]
    s = client.get("/journal/summary", headers=h).json()
    assert s["streak"] == 6 and s["logged_today"] and s["count"] == 5
    assert s["last"]["mood"] == 3.4 and s["previous"]["mood"] == 2.0 and s["last"]["sleep"] == 6.2
    assert client.post("/journal", json={"mood": 3, "sleep_hours": 30}, headers=h).status_code == 422
    assert client.post("/journal", json={"mood": 3, "tags": list("abcdefg")}, headers=h).status_code == 422


def test_safety_plan_full_and_crisis_text():
    h = signup("p@b.com")
    plan = {"contact_name": "Amma", "contact_phone": "00000 00000", "contact2_name": "Friend",
            "contact2_phone": "11111 11111", "coping_steps": "walk, music", "safe_place": "terrace",
            "warning_signs": "not sleeping", "reasons": "my family", "make_safe": "ask Amma to keep medicines"}
    assert client.put("/safety-plan", json=plan, headers=h).json()["saved"]
    assert client.get("/safety-plan", headers=h).json() == plan
    r = client.post("/chat", json={"message": "I want to die", "language": "en"}, headers=h).json()["reply"]
    assert "Amma" in r and "Friend" in r and "my family" in r and "not sleeping" not in r


def test_old_database_is_migrated():
    con = sqlite3.connect(DBFILE)
    con.execute("DROP TABLE mood_entries")
    con.execute("CREATE TABLE mood_entries (id INTEGER PRIMARY KEY, user_id INTEGER, day DATE, mood INTEGER, "
                "note TEXT, created_at DATETIME)")
    con.commit()
    con.close()
    from app import extras
    from app.db import engine
    extras.migrate(engine)
    h = signup("old@b.com")
    assert client.post("/journal", json={"mood": 3, "sleep_hours": 7}, headers=h).json()["sleep_hours"] == 7


def test_programs_catalogue():
    h = signup("g@b.com")
    progs = client.get("/programs", headers=h).json()
    assert len(progs) >= 6 and all(p["days"] and all(d["minutes"] > 0 for d in p["days"]) for p in progs)


def test_llm_rules_and_checks():
    assert llm.generate("Should I take medicine for anxiety?", [], "en")[1] == "rule"
    assert llm.generate("I feel lonely", [], "en")[1] == "fallback"  # no model or Gemini configured in tests
    assert llm._check("Talk to your doctor about medication options.") is None
    assert llm._check("Visit https://example.com") == "url"
    assert llm._check("Take 50 mg of sertraline") == "medication"
    assert llm._check("You have depression.") == "diagnosis"
    assert llm._check("word " * 90) == "too_long"
    assert llm._non_latin("मुझे तनाव है") and not llm._non_latin("estoy cansado, ¿qué hago?")
