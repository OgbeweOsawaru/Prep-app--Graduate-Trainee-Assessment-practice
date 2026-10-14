from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

import config
from attempt import Attempt, create_attempt, get_attempt
from bank import load_bank
from grader import grade
from schemas import ResultsResponse, StartResponse, SubmitRequest, SubmitResponse

router = APIRouter(prefix="/tests", tags=["tests"])

# Loaded once, when the app starts. A broken CSV stops the app right here.
bank = load_bank()


def api_error(status: int, code: str, message: str) -> HTTPException:
    """Build an error whose body is {"detail": {"code": ..., "message": ...}}."""
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def get_attempt_or_404(attempt_id: str) -> Attempt:
    attempt = get_attempt(attempt_id)
    if attempt is None:
        raise api_error(404, "attempt_not_found", "No attempt with that id.")
    return attempt


@router.post("", response_model=StartResponse, status_code=201)
def start_test():
    attempt = create_attempt(bank)
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
def submit_test(attempt_id: str, body: SubmitRequest):
    attempt = get_attempt_or_404(attempt_id)

    # 1. Already handed in?
    if attempt.submitted_at is not None:
        raise api_error(409, "already_submitted", "This attempt was already submitted.")

    # 2. Too late? The server's clock decides, not the browser's.
    now = datetime.now(timezone.utc)
    if now > attempt.deadline + timedelta(seconds=config.GRACE_SECONDS):
        raise api_error(409, "deadline_passed", "The time limit has passed.")

    # 3. Only questions from this attempt may be answered.
    valid_ids = {q.id for q in attempt.questions}
    unknown = set(body.answers) - valid_ids
    if unknown:
        raise api_error(
            422, "unknown_question", f"Not part of this attempt: {sorted(unknown)}"
        )

    attempt.answers = dict(body.answers)
    attempt.submitted_at = now
    return SubmitResponse(status="submitted")


@router.get("/{attempt_id}/results", response_model=ResultsResponse)
def get_results(attempt_id: str):
    attempt = get_attempt_or_404(attempt_id)

    # Refuse until submitted, otherwise this endpoint would leak the answers.
    if attempt.submitted_at is None:
        raise api_error(409, "not_submitted", "Submit the test to see results.")

    overall, sections, review = grade(attempt.questions, attempt.answers)
    taken = attempt.submitted_at - attempt.started_at
    return ResultsResponse(
        attempt_id=attempt.attempt_id,
        submitted_at=attempt.submitted_at,
        time_taken_seconds=int(taken.total_seconds()),
        overall=overall,
        sections=sections,
        review=review,
    )
