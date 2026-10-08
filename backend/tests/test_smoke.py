import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/test.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ.pop("MODEL_SERVER_URL", None)
os.environ.pop("GEMINI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app import safety  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def auth():
    r = client.post("/auth/signup", json={"email": "a@b.com", "password": "password123", "name": "A"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_flow():
    h = auth()
    assert client.post("/auth/login", json={"email": "a@b.com", "password": "wrong-pass"}).status_code == 401
    assert client.post("/auth/signup", json={"email": "a@b.com", "password": "password123"}).status_code == 409
    assert client.get("/conversations").status_code in (401, 403)

    r = client.post("/chat", json={"message": "I have exams and feel stressed", "language": "en"}, headers=h)
    assert r.status_code == 200 and not r.json()["is_crisis"]
    cid = r.json()["conversation_id"]

    r = client.post("/chat", json={"message": "I want to die", "language": "en", "conversation_id": cid}, headers=h)
    assert r.json()["is_crisis"] and "14416" in r.json()["reply"] and r.json()["source"] == "safety"

    assert len(client.get(f"/conversations/{cid}", headers=h).json()["messages"]) == 4
    assert len(client.get("/helplines?country=IN&lang=hi").json()) >= 1
    assert "quote" in client.get("/quote").json()
    assert client.delete(f"/conversations/{cid}", headers=h).json()["deleted"]
    assert client.delete("/me", headers=h).json()["deleted"]


def test_safety():
    assert safety.is_crisis("quiero morir") and safety.is_crisis("मैं आत्महत्या करना चाहता हूँ")
    assert not safety.is_crisis("I have exams next week")
    assert safety.guard("Sí, es posible que tengas ansiedad.", "es") != "Sí, es posible que tengas ansiedad."
    assert safety.guard("It's possible that what you're experiencing is depression.", "en").startswith("I can't diagnose")
    assert safety.guard("Try slow breathing for a minute.", "en") == "Try slow breathing for a minute."
