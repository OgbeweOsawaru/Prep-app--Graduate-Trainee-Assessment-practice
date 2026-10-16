from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True,)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )

    questions: Mapped[list[AttemptQuestion]] = relationship(
        back_populates="attempt",
        order_by="AttemptQuestion.position",
        cascade="all, delete-orphan",
    )
    answers: Mapped[list[Answer]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan",
    )


class AttemptQuestion(Base):
    __tablename__ = "attempt_questions"

    attempt_id: Mapped[str] = mapped_column(
        ForeignKey("attempts.id"), primary_key=True
    )
    position: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[str] = mapped_column(String)

    attempt: Mapped[Attempt] = relationship(back_populates="questions")


class Answer(Base):
    __tablename__ = "answers"

    attempt_id: Mapped[str] = mapped_column(
        ForeignKey("attempts.id"), primary_key=True
    )
    question_id: Mapped[str] = mapped_column(String, primary_key=True)
    chosen: Mapped[str] = mapped_column(String(1))

    attempt: Mapped[Attempt] = relationship(back_populates="answers")