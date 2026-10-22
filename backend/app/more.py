"""Reply feedback (thumbs up/down) and guided self-care programs."""
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, Session, mapped_column

from .auth import current_user
from .db import Base, Conversation, Message, User, get_db, now

PROGRAMS = json.loads((Path(__file__).parent / "data" / "programs.json").read_text(encoding="utf-8"))


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (UniqueConstraint("user_id", "message_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message_id: Mapped[int] = mapped_column(index=True)
    rating: Mapped[int]  # 1 = helpful, -1 = not helpful
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ProgramProgress(Base):
    __tablename__ = "program_progress"
    __table_args__ = (UniqueConstraint("user_id", "program_id", "day"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    program_id: Mapped[str] = mapped_column(String(50))
    day: Mapped[int]
    done_at: Mapped[datetime] = mapped_column(DateTime, default=now)


router = APIRouter()


class FeedbackReq(BaseModel):
    message_id: int
    rating: int = Field(ge=-1, le=1)
    comment: str = Field(default="", max_length=300)


@router.post("/feedback")
def feedback(req: FeedbackReq, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if req.rating == 0:
        raise HTTPException(422, "Rating must be 1 or -1")
    msg = db.get(Message, req.message_id)
    conv = db.get(Conversation, msg.conversation_id) if msg else None
    if not msg or msg.role != "assistant" or conv.user_id != user.id:
        raise HTTPException(404, "Message not found")
    fb = db.query(Feedback).filter_by(user_id=user.id, message_id=msg.id).first() or \
        Feedback(user_id=user.id, message_id=msg.id, rating=req.rating)
    fb.rating, fb.comment = req.rating, req.comment
    db.add(fb)
    db.commit()
    return {"saved": True}


@router.get("/programs")
def programs(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(ProgramProgress).filter_by(user_id=user.id).all()
    return [{**p, "done": sorted(r.day for r in rows if r.program_id == p["id"])} for p in PROGRAMS]


def _check(program_id: str, day: int):
    prog = next((p for p in PROGRAMS if p["id"] == program_id), None)
    if not prog or day not in [d["day"] for d in prog["days"]]:
        raise HTTPException(404, "Program day not found")


@router.post("/programs/{program_id}/days/{day}")
def complete_day(program_id: str, day: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _check(program_id, day)
    if not db.query(ProgramProgress).filter_by(user_id=user.id, program_id=program_id, day=day).first():
        db.add(ProgramProgress(user_id=user.id, program_id=program_id, day=day))
        db.commit()
    return {"done": True}


@router.delete("/programs/{program_id}/days/{day}")
def undo_day(program_id: str, day: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    _check(program_id, day)
    db.query(ProgramProgress).filter_by(user_id=user.id, program_id=program_id, day=day).delete()
    db.commit()
    return {"done": False}


def delete_feedback_for(db: Session, message_ids: list[int]) -> None:
    if message_ids:
        db.query(Feedback).filter(Feedback.message_id.in_(message_ids)).delete(synchronize_session=False)


def delete_user_data(db: Session, user_id: int) -> None:
    db.query(Feedback).filter_by(user_id=user_id).delete()
    db.query(ProgramProgress).filter_by(user_id=user_id).delete()
