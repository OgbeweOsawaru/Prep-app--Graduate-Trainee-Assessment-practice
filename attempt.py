from dataclasses import dataclass,field
import random
from bank import load_bank
from datetime import datetime, timedelta, timezone 
import config
from uuid import uuid4
from schemas import Question
from sqlalchemy.orm import Session
from database import SessionLocal
from sqlalchemy import select
from models import Attempt as AttemptModel, AttemptQuestion,SeenQuestions

bank = load_bank()
def get_seen_ids(db:Session,user_id:int):
    statement=select(SeenQuestions).where(SeenQuestions.user_id==user_id)
    result=db.scalars(statement).all()
    question_id=[]
    for question in result:
        question_id.append(question.question_id)
    return set(question_id)
def build_test(bank: list[Question], seen):
    build = []
    for i in config.BLUEPRINT:
        need = config.BLUEPRINT[i]
        unseen = [row for row in bank if row.section == i and row.id not in seen]
        seen_rows = [row for row in bank if row.section == i and row.id in seen]
        if len(unseen) >= need:
            build.extend(random.sample(unseen, need))
        else:
            build.extend(unseen)
            build.extend(random.sample(seen_rows, need - len(unseen)))
    return build


@dataclass
class Attempt:
    """One person's test. Lives only in memory (SQLite comes in Phase 3)."""
    attempt_id: str
    questions: list[Question]
    started_at: datetime
    deadline: datetime
    answers: dict[str, str | None] = field(default_factory=dict)
    submitted_at: datetime | None = None
 
 
# attempt_id -> Attempt. Wiped when the server restarts.
_attempts: dict[str, Attempt] = {}
 
 
def create_attempt(bank: list[Question],seen) -> Attempt:
    now = datetime.now(timezone.utc)
    attempt = Attempt(
        attempt_id=str(uuid4()),  # unguessable, because it acts as a password
        questions=build_test(bank,seen),
        started_at=now,
        deadline=now + timedelta(seconds=config.TIME_LIMIT_SECONDS),
    )
    _attempts[attempt.attempt_id] = attempt
    return attempt
 
 
def get_attempt(attempt_id: str) -> Attempt | None:
    return _attempts.get(attempt_id)
if __name__ == "__main__":
   
    db=SessionLocal()
    #print(get_seen_ids(db,1))
    print(len(get_seen_ids(db,4)))
    db.close()
    """bank = load_bank()
    attempt = create_attempt(bank)
    print(len(attempt.questions))
    print(attempt.deadline - attempt.started_at)
    print(attempt.attempt_id in _attempts)
    print(attempt.questions[0].section, attempt.questions[25].section, attempt.questions[50].section)"""
#a=build_test(load_bank())
#print(len(a))
