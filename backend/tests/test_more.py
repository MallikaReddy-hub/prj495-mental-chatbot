import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/t3.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ.pop("MODEL_SERVER_URL", None)
os.environ.pop("GEMINI_API_KEY", None)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def signup(email):
    r = client.post("/auth/signup", json={"email": email, "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_feedback_and_programs():
    a, b = signup("fa@b.com"), signup("fb@b.com")
    chat = client.post("/chat", json={"message": "hello there", "language": "en"}, headers=a).json()
    mid = chat["message_id"]
    assert client.post("/feedback", json={"message_id": mid, "rating": 1}, headers=a).json()["saved"]
    assert client.post("/feedback", json={"message_id": mid, "rating": -1}, headers=a).json()["saved"]  # update
    assert client.post("/feedback", json={"message_id": mid, "rating": 0}, headers=a).status_code == 422
    assert client.post("/feedback", json={"message_id": mid, "rating": 1}, headers=b).status_code == 404  # not theirs

    conv = client.get(f"/conversations/{chat['conversation_id']}", headers=a).json()
    assert all("id" in m for m in conv["messages"])

    progs = client.get("/programs", headers=a).json()
    assert len(progs) >= 2 and progs[0]["done"] == []
    pid = progs[0]["id"]
    assert client.post(f"/programs/{pid}/days/1", headers=a).json()["done"]
    client.post(f"/programs/{pid}/days/1", headers=a)  # idempotent
    client.post(f"/programs/{pid}/days/2", headers=a)
    assert client.get("/programs", headers=a).json()[0]["done"] == [1, 2]
    assert client.get("/programs", headers=b).json()[0]["done"] == []
    assert client.delete(f"/programs/{pid}/days/2", headers=a).json()["done"] is False
    assert client.post(f"/programs/{pid}/days/99", headers=a).status_code == 404

    assert client.delete(f"/conversations/{chat['conversation_id']}", headers=a).json()["deleted"]
    assert client.delete("/me", headers=a).json()["deleted"]
