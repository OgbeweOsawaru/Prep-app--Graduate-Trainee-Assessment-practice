from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String,Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

class User(Base):
    __tablename__="users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str]=mapped_column(String(200),nullable=False)
    user_attempts: Mapped[list[Attempt]] = relationship(
            back_populates="user",
            order_by="Attempt.id",
        )
class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String, primary_key=True,)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),default=None,
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
    user:Mapped[User|None]=relationship(back_populates="user_attempts")


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