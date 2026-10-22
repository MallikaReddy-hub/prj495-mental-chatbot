"""Mood journal and personal safety plan."""
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, Session, mapped_column

from .auth import current_user
from .db import Base, User, get_db, now


class MoodEntry(Base):
    __tablename__ = "mood_entries"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    day: Mapped[date] = mapped_column(Date)
    mood: Mapped[int]
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class SafetyPlan(Base):
    __tablename__ = "safety_plans"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    contact_name: Mapped[str] = mapped_column(String(100), default="")
    contact_phone: Mapped[str] = mapped_column(String(30), default="")
    coping_steps: Mapped[str] = mapped_column(Text, default="")
    safe_place: Mapped[str] = mapped_column(String(200), default="")


router = APIRouter()


class MoodReq(BaseModel):
    mood: int = Field(ge=1, le=5)
    note: str = Field(default="", max_length=500)
    day: date | None = None


class PlanReq(BaseModel):
    contact_name: str = Field(default="", max_length=100)
    contact_phone: str = Field(default="", max_length=30)
    coping_steps: str = Field(default="", max_length=800)
    safe_place: str = Field(default="", max_length=200)


@router.post("/journal")
def save_mood(req: MoodReq, user: User = Depends(current_user), db: Session = Depends(get_db)):
    day = req.day or date.today()
    entry = db.query(MoodEntry).filter_by(user_id=user.id, day=day).first()  # one entry per day
    if entry:
        entry.mood, entry.note = req.mood, req.note
    else:
        entry = MoodEntry(user_id=user.id, day=day, mood=req.mood, note=req.note)
        db.add(entry)
    db.commit()
    return {"id": entry.id, "day": str(entry.day), "mood": entry.mood, "note": entry.note}


@router.get("/journal")
def list_moods(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = (db.query(MoodEntry).filter_by(user_id=user.id)
            .order_by(MoodEntry.day.desc()).limit(30).all())
    return [{"id": r.id, "day": str(r.day), "mood": r.mood, "note": r.note} for r in reversed(rows)]


@router.delete("/journal/{entry_id}")
def delete_mood(entry_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    entry = db.get(MoodEntry, entry_id)
    if not entry or entry.user_id != user.id:
        raise HTTPException(404, "Entry not found")
    db.delete(entry)
    db.commit()
    return {"deleted": True}


@router.get("/safety-plan")
def get_plan(user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(SafetyPlan, user.id)
    return {"contact_name": p.contact_name, "contact_phone": p.contact_phone,
            "coping_steps": p.coping_steps, "safe_place": p.safe_place} if p else \
           {"contact_name": "", "contact_phone": "", "coping_steps": "", "safe_place": ""}


@router.put("/safety-plan")
def save_plan(req: PlanReq, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(SafetyPlan, user.id) or SafetyPlan(user_id=user.id)
    p.contact_name, p.contact_phone = req.contact_name, req.contact_phone
    p.coping_steps, p.safe_place = req.coping_steps, req.safe_place
    db.add(p)
    db.commit()
    return {"saved": True}


def plan_text(db: Session, user_id: int) -> str:
    """Text appended to a crisis reply, or '' if the user has no plan."""
    p = db.get(SafetyPlan, user_id)
    if not p or not (p.contact_name or p.contact_phone or p.coping_steps or p.safe_place):
        return ""
    lines = ["\n\nYour own safety plan:"]
    if p.contact_name or p.contact_phone:
        lines.append(f"- Reach out to: {p.contact_name} {p.contact_phone}".rstrip())
    if p.coping_steps:
        lines.append(f"- Things that help you: {p.coping_steps}")
    if p.safe_place:
        lines.append(f"- A safe place for you: {p.safe_place}")
    return "\n".join(lines)


def delete_user_data(db: Session, user_id: int) -> None:
    db.query(MoodEntry).filter_by(user_id=user_id).delete()
    db.query(SafetyPlan).filter_by(user_id=user_id).delete()
