from datetime import datetime, timedelta, timezone
from models import Attempt as AttemptModel, AttemptQuestion,Answer,User,SeenQuestions
from fastapi import APIRouter, HTTPException,Depends
from sqlalchemy.orm import Session
from database import get_db
import config
from attempt import Attempt, create_attempt, get_attempt,get_seen_ids
from bank import load_bank
from grader import grade
from schemas import ResultsResponse, StartResponse, SubmitRequest, SubmitResponse
from deps import get_current_user
from sqlalchemy import select, func
router = APIRouter(prefix="/tests", tags=["tests"])

# Loaded once, when the app starts. A broken CSV stops the app right here.
bank = load_bank()
bank_by_id = {q.id: q for q in bank}

def api_error(status: int, code: str, message: str) -> HTTPException:
    """Build an error whose body is {"detail": {"code": ..., "message": ...}}."""
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def get_attempt_or_404(attempt_id: str) -> Attempt:
    attempt = get_attempt(attempt_id)
    if attempt is None:
        raise api_error(404, "attempt_not_found", "No attempt with that id.")
    return attempt


@router.post("", response_model=StartResponse, status_code=201)
def start_test(current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    started = db.scalar(
    select(func.count())
    .select_from(AttemptModel)
    .where(AttemptModel.user_id == current_user.id)
    )
    if started>= config.MAX_FREE_TESTS:
        raise api_error(402, "attempt_not_allowed", "No more free attempts.")
    seen=get_seen_ids(db, current_user.id)
    attempt = create_attempt(bank,seen)
    db_attempt = AttemptModel(
    id=attempt.attempt_id,
    started_at=attempt.started_at,
    deadline=attempt.deadline,
    user_id= current_user.id)
    for position, q in enumerate(attempt.questions, start=1):
        db_attempt.questions.append(
            AttemptQuestion(position=position, question_id=q.id)
        )
    for row in attempt.questions:
        if row.id not in seen:
            seen_rows=SeenQuestions(
                user_id=current_user.id,
                question_id=row.id
            )
            db.add(seen_rows)
    db.add(db_attempt)
    db.commit()
    return StartResponse(
        attempt_id=attempt.attempt_id,
        started_at=attempt.started_at,
        deadline=attempt.deadline,
        duration_seconds=config.TIME_LIMIT_SECONDS,
        server_time=datetime.now(timezone.utc),
        # to_public() strips the answer and explanation
        questions=[q.to_public() for q in attempt.questions],
    )


@router.post("/{attempt_id}/submit", response_model=SubmitResponse)
def submit_test(
    attempt_id: str,
    body: SubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ):
    db_attempt = db.get(AttemptModel, attempt_id)
    if db_attempt is None or db_attempt.user_id != current_user.id:
        raise api_error(404, "attempt_not_found", "No attempt with that id.")

    # 1. Already handed in?
    if db_attempt.submitted_at is not None:
        raise api_error(409, "already_submitted", "This attempt was already submitted.")

    # 2. Too late? The server's clock decides, not the browser's.
    now = datetime.now(timezone.utc)
    deadline = db_attempt.deadline.replace(tzinfo=timezone.utc)
    if now > deadline + timedelta(seconds=config.GRACE_SECONDS):
        raise api_error(409, "deadline_passed", "The time limit has passed.")

    # 3. Only questions from this attempt may be answered.
    valid_ids = {aq.question_id for aq in db_attempt.questions}
    unknown = set(body.answers) - valid_ids
    if unknown:
        raise api_error(
            422, "unknown_question", f"Not part of this attempt: {sorted(unknown)}"
        )
    db_attempt = db.get(AttemptModel, attempt_id)
    for question_id, chosen in body.answers.items():
        db_attempt.answers.append(
            Answer(question_id=question_id, chosen=chosen)
        )
    db_attempt.submitted_at = now
    db.commit()
    return SubmitResponse(status="submitted")


@router.get("/{attempt_id}/results", response_model=ResultsResponse)
def get_results(
    attempt_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ):
    db_attempt = db.get(AttemptModel, attempt_id)
    if db_attempt is None or db_attempt.user_id != current_user.id:
        raise api_error(404, "attempt_not_found", "No attempt with that id.")
    # Refuse until submitted, otherwise this endpoint would leak the answers.
    if db_attempt.submitted_at is None:
        raise api_error(409, "not_submitted", "Submit the test to see results.")
    saved_answers = {a.question_id: a.chosen for a in db_attempt.answers}
    saved_questions = [bank_by_id[aq.question_id] for aq in db_attempt.questions]
    overall, sections, review = grade(saved_questions, saved_answers)
    taken = db_attempt.submitted_at - db_attempt.started_at
    return ResultsResponse(
        attempt_id=db_attempt.id,
        submitted_at=db_attempt.submitted_at,
        time_taken_seconds=int(taken.total_seconds()),
        overall=overall,
        sections=sections,
        review=review,
    )
