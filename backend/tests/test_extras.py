import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t2.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ.pop("MODEL_SERVER_URL", None)
os.environ.pop("GEMINI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_journal_plan_and_crisis():
    r = client.post("/auth/signup", json={"email": "j@b.com", "password": "password123"})
    h = {"Authorization": f"Bearer {r.json()['token']}"}

    assert client.post("/journal", json={"mood": 9}, headers=h).status_code == 422
    first = client.post("/journal", json={"mood": 2, "note": "tough day"}, headers=h).json()
    again = client.post("/journal", json={"mood": 4}, headers=h).json()
    assert first["id"] == again["id"]                      # same day updates, no duplicate
    rows = client.get("/journal", headers=h).json()
    assert len(rows) == 1 and rows[0]["mood"] == 4

    client.put("/safety-plan", json={"contact_name": "Amma", "contact_phone": "99999 00000",
                                     "coping_steps": "walk, music", "safe_place": "terrace"}, headers=h)
    assert client.get("/safety-plan", headers=h).json()["contact_name"] == "Amma"

    reply = client.post("/chat", json={"message": "I want to die", "language": "en"}, headers=h).json()
    assert reply["is_crisis"] and "Amma" in reply["reply"] and "14416" in reply["reply"]

    assert client.delete(f"/journal/{rows[0]['id']}", headers=h).json()["deleted"]
    assert client.delete("/me", headers=h).json()["deleted"]
    # all data gone: the same email can sign up again with an empty journal
    r2 = client.post("/auth/signup", json={"email": "j@b.com", "password": "password123"})
    h2 = {"Authorization": f"Bearer {r2.json()['token']}"}
    assert client.get("/journal", headers=h2).json() == []
    assert client.get("/safety-plan", headers=h2).json()["contact_name"] == ""
