from dataclasses import dataclass,field
import random
from bank import load_bank
from datetime import datetime, timedelta, timezone 
import config
from uuid import uuid4
from schemas import Question
def build_test(bank: list[Question]):
    build=[]
    for i in config.BLUEPRINT:
        rows=[row for row in bank if row.section==i]
        build.extend(random.sample(rows, config.BLUEPRINT[i]))
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
 
 
def create_attempt(bank: list[Question]) -> Attempt:
    now = datetime.now(timezone.utc)
    attempt = Attempt(
        attempt_id=str(uuid4()),  # unguessable, because it acts as a password
        questions=build_test(bank),
        started_at=now,
        deadline=now + timedelta(seconds=config.TIME_LIMIT_SECONDS),
    )
    _attempts[attempt.attempt_id] = attempt
    return attempt
 
 
def get_attempt(attempt_id: str) -> Attempt | None:
    return _attempts.get(attempt_id)
if __name__ == "__main__":
    bank = load_bank()
    attempt = create_attempt(bank)
    print(len(attempt.questions))
    print(attempt.deadline - attempt.started_at)
    print(attempt.attempt_id in _attempts)
    print(attempt.questions[0].section, attempt.questions[25].section, attempt.questions[50].section)
#a=build_test(load_bank())
#print(len(a))
