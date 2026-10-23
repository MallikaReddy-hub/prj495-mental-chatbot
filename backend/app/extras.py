"""Mood journal (mood, sleep, tags, streak, summary) and personal safety plan."""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, inspect, text
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
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    tags: Mapped[str] = mapped_column(String(200), default="")  # comma separated
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class SafetyPlan(Base):
    __tablename__ = "safety_plans"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    contact_name: Mapped[str] = mapped_column(String(100), default="")
    contact_phone: Mapped[str] = mapped_column(String(30), default="")
    coping_steps: Mapped[str] = mapped_column(Text, default="")
    safe_place: Mapped[str] = mapped_column(String(200), default="")
    contact2_name: Mapped[str] = mapped_column(String(100), default="")
    contact2_phone: Mapped[str] = mapped_column(String(30), default="")
    warning_signs: Mapped[str] = mapped_column(Text, default="")
    reasons: Mapped[str] = mapped_column(Text, default="")
    make_safe: Mapped[str] = mapped_column(Text, default="")


# columns added after the first release; migrate() adds them to an existing database
NEW_COLUMNS = {
    "mood_entries": {"sleep_hours": "FLOAT", "tags": "VARCHAR(200) DEFAULT ''"},
    "safety_plans": {"contact2_name": "VARCHAR(100) DEFAULT ''", "contact2_phone": "VARCHAR(30) DEFAULT ''",
                     "warning_signs": "TEXT DEFAULT ''", "reasons": "TEXT DEFAULT ''",
                     "make_safe": "TEXT DEFAULT ''"},
}


def migrate(engine) -> None:
    """create_all never alters existing tables, so add any missing new columns."""
    insp = inspect(engine)
    with engine.begin() as conn:
        for table, cols in NEW_COLUMNS.items():
            if not insp.has_table(table):
                continue
            have = {c["name"] for c in insp.get_columns(table)}
            for name, ddl in cols.items():
                if name not in have:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


PROMPTS = [
    "One thing that went a little better than I expected today:",
    "Something I'm grateful for right now:",
    "What is weighing on me the most today?",
    "One kind thing I did for myself or someone else:",
    "What would make tomorrow 1% easier?",
    "A moment today when I felt calm, even briefly:",
    "Something I'm proud of this week:",
]
PLAN_FIELDS = ["contact_name", "contact_phone", "contact2_name", "contact2_phone", "coping_steps",
               "safe_place", "warning_signs", "reasons", "make_safe"]

router = APIRouter()


class MoodReq(BaseModel):
    mood: int = Field(ge=1, le=5)
    note: str = Field(default="", max_length=500)
    day: date | None = None
    sleep_hours: float | None = Field(default=None, ge=0, le=16)
    tags: list[str] = Field(default_factory=list, max_length=6)


class PlanReq(BaseModel):
    contact_name: str = Field(default="", max_length=100)
    contact_phone: str = Field(default="", max_length=30)
    contact2_name: str = Field(default="", max_length=100)
    contact2_phone: str = Field(default="", max_length=30)
    coping_steps: str = Field(default="", max_length=800)
    safe_place: str = Field(default="", max_length=200)
    warning_signs: str = Field(default="", max_length=800)
    reasons: str = Field(default="", max_length=800)
    make_safe: str = Field(default="", max_length=800)


def _clean_tags(tags: list[str]) -> str:
    seen: list[str] = []
    for t in tags:
        t = " ".join(t.strip().lower().replace(",", " ").split())[:20]
        if t and t not in seen:
            seen.append(t)
    return ",".join(seen[:6])


def _row(r: MoodEntry) -> dict:
    return {"id": r.id, "day": str(r.day), "mood": r.mood, "note": r.note,
            "sleep_hours": r.sleep_hours, "tags": [t for t in (r.tags or "").split(",") if t]}


@router.post("/journal")
def save_mood(req: MoodReq, user: User = Depends(current_user), db: Session = Depends(get_db)):
    day = req.day or date.today()
    entry = db.query(MoodEntry).filter_by(user_id=user.id, day=day).first()  # one entry per day
    if entry:
        entry.mood, entry.note = req.mood, req.note
        entry.sleep_hours, entry.tags = req.sleep_hours, _clean_tags(req.tags)
    else:
        entry = MoodEntry(user_id=user.id, day=day, mood=req.mood, note=req.note,
                          sleep_hours=req.sleep_hours, tags=_clean_tags(req.tags))
        db.add(entry)
    db.commit()
    return _row(entry)


@router.get("/journal")
def list_moods(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = (db.query(MoodEntry).filter_by(user_id=user.id)
            .order_by(MoodEntry.day.desc()).limit(30).all())
    return [_row(r) for r in reversed(rows)]


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 1) if values else None


@router.get("/journal/summary")
def mood_summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    """Average mood/sleep of the last 5 check-ins vs the 5 before, streak and today's prompt."""
    rows = db.query(MoodEntry).filter_by(user_id=user.id).order_by(MoodEntry.day.desc()).limit(60).all()
    last, prev = rows[:5], rows[5:10]
    days = {r.day for r in rows}
    cursor = date.today() if date.today() in days else date.today() - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)

    def block(group):
        return {"mood": _avg([r.mood for r in group]),
                "sleep": _avg([r.sleep_hours for r in group if r.sleep_hours is not None])}

    return {"last": block(last), "previous": block(prev), "count": len(last), "streak": streak,
            "logged_today": date.today() in days, "prompt": PROMPTS[date.today().toordinal() % len(PROMPTS)]}


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
    return {k: (getattr(p, k) or "") if p else "" for k in PLAN_FIELDS}


@router.put("/safety-plan")
def save_plan(req: PlanReq, user: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.get(SafetyPlan, user.id) or SafetyPlan(user_id=user.id)
    for k in PLAN_FIELDS:
        setattr(p, k, getattr(req, k))
    db.add(p)
    db.commit()
    return {"saved": True}


def plan_text(db: Session, user_id: int) -> str:
    """Text appended to a crisis reply, or '' if the user has no plan."""
    p = db.get(SafetyPlan, user_id)
    if not p or not any(getattr(p, k) for k in PLAN_FIELDS if k != "warning_signs"):
        return ""
    lines = ["\n\nYour own safety plan:"]
    for name, phone in ((p.contact_name, p.contact_phone), (p.contact2_name, p.contact2_phone)):
        if name or phone:
            lines.append(f"- Reach out to: {name} {phone}".rstrip())
    if p.coping_steps:
        lines.append(f"- Things that help you: {p.coping_steps}")
    if p.safe_place:
        lines.append(f"- A safe place for you: {p.safe_place}")
    if p.make_safe:
        lines.append(f"- Making your space safer: {p.make_safe}")
    if p.reasons:
        lines.append(f"- Your reasons to keep going: {p.reasons}")
    return "\n".join(lines)


def delete_user_data(db: Session, user_id: int) -> None:
    db.query(MoodEntry).filter_by(user_id=user_id).delete()
    db.query(SafetyPlan).filter_by(user_id=user_id).delete()
