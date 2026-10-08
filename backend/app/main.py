import json
import os
from datetime import date
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import llm, safety
from .auth import create_token, current_user, hash_password, verify_password
from .db import Base, Conversation, Message, User, engine, get_db

DATA = Path(__file__).parent / "data"
HELPLINES = json.loads((DATA / "helplines.json").read_text(encoding="utf-8"))
QUOTES = json.loads((DATA / "quotes.json").read_text(encoding="utf-8"))
LANGS = {"en", "hi", "te", "ta", "kn", "es"}
DEFAULT_COUNTRY = os.getenv("DEFAULT_COUNTRY", "IN")

Base.metadata.create_all(engine)
app = FastAPI(title="PRJ_495 Mental Health Chatbot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"], allow_headers=["*"])


class SignupReq(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=72)
    name: str = Field(default="", max_length=100)


class LoginReq(BaseModel):
    email: str
    password: str


class ChatReq(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    language: str = "en"
    conversation_id: int | None = None


def helplines_for(country: str, lang: str | None = None) -> list[dict]:
    items = HELPLINES.get(country.upper(), [])
    matching = [h for h in items if not lang or lang in h["lang"]]
    return matching or items


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/auth/signup")
def signup(req: SignupReq, db: Session = Depends(get_db)):
    email = req.email.lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "Email already registered")
    user = User(email=email, name=req.name, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    return {"token": create_token(user.id), "name": user.name}


@app.post("/auth/login")
def login(req: LoginReq, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=req.email.lower()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": create_token(user.id), "name": user.name}


@app.get("/me")
def me(user: User = Depends(current_user)):
    return {"email": user.email, "name": user.name}


@app.get("/helplines")
def helplines(country: str = DEFAULT_COUNTRY, lang: str | None = None):
    return helplines_for(country, lang)


@app.get("/quote")
def quote():
    return {"quote": QUOTES[date.today().toordinal() % len(QUOTES)]}


@app.post("/chat")
def chat(req: ChatReq, user: User = Depends(current_user), db: Session = Depends(get_db)):
    lang = req.language if req.language in LANGS else "en"
    if req.conversation_id:
        conv = db.get(Conversation, req.conversation_id)
        if not conv or conv.user_id != user.id:
            raise HTTPException(404, "Conversation not found")
    else:
        conv = Conversation(user_id=user.id, title=req.message[:40])
        db.add(conv)
        db.flush()
    history = [{"role": m.role, "content": m.content} for m in conv.messages[-6:]]
    db.add(Message(conversation_id=conv.id, role="user", content=req.message))

    if safety.is_crisis(req.message):
        reply = safety.crisis_message(lang, helplines_for(DEFAULT_COUNTRY, lang))
        crisis, source = True, "safety"
    else:
        reply, source = llm.generate(req.message, history, lang)
        reply, crisis = safety.guard(reply, lang), False

    db.add(Message(conversation_id=conv.id, role="assistant", content=reply, is_crisis=crisis))
    db.commit()
    return {"reply": reply, "is_crisis": crisis, "conversation_id": conv.id, "source": source}


@app.get("/conversations")
def list_conversations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = (db.query(Conversation).filter_by(user_id=user.id)
            .order_by(Conversation.id.desc()).all())
    return [{"id": c.id, "title": c.title, "created_at": c.created_at} for c in rows]


@app.get("/conversations/{conv_id}")
def get_conversation(conv_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = db.get(Conversation, conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(404, "Conversation not found")
    return {"id": conv.id, "title": conv.title, "messages": [
        {"role": m.role, "content": m.content, "is_crisis": m.is_crisis, "created_at": m.created_at}
        for m in conv.messages]}


@app.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conv = db.get(Conversation, conv_id)
    if not conv or conv.user_id != user.id:
        raise HTTPException(404, "Conversation not found")
    db.delete(conv)
    db.commit()
    return {"deleted": True}


@app.delete("/me")
def delete_account(user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(user)  # conversations and messages cascade
    db.commit()
    return {"deleted": True}
