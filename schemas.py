from datetime import datetime
from typing import Literal

from pydantic import BaseModel,Field,EmailStr,ConfigDict

# Allowed values. If you ever rename a section, change it here AND in config.py.
Section = Literal["numerical", "verbal", "critical"]
Letter = Literal["a", "b", "c", "d", "e"]


class Options(BaseModel):
    """The five answer options, as {a: ..., b: ..., ...} (matches API.md)."""
    a: str
    b: str
    c: str
    d: str
    e: str


# ---------- Questions ----------

class PublicQuestion(BaseModel):
    """What the browser is allowed to see. Note: no answer, no explanation."""
    id: str
    section: Section
    passage: str | None = None
    question: str
    options: Options


class Question(PublicQuestion):
    """Internal bank question. Never sent to the browser as-is."""
    answer: Letter
    explanation: str

    def to_public(self) -> PublicQuestion:
        # Drop the two secret fields, keep the rest.
        return PublicQuestion(**self.model_dump(exclude={"answer", "explanation"}))


# ---------- Start ----------

class StartResponse(BaseModel):
    attempt_id: str
    started_at: datetime
    deadline: datetime
    duration_seconds: int
    server_time: datetime
    questions: list[PublicQuestion]
    

# Register 
class RegisterRequest(BaseModel):
    username:str= Field(min_length=1, max_length=50)
    email:EmailStr=Field(max_length=120)
    password:str=Field(min_length=4,max_length=120)
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username:str= Field(min_length=1, max_length=50)
    email:EmailStr=Field(max_length=120)
    id:int
class LoginRequest(BaseModel):
    email:EmailStr=Field(max_length=120)
    password:str=Field(max_length=120)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
# ---------- Submit ----------

class SubmitRequest(BaseModel):
    # question id -> chosen letter. A skipped question is missing or None.
    # Pydantic rejects any value that isn't a-e (FastAPI returns 422 for us).
    answers: dict[str, Letter | None] = {}


class SubmitResponse(BaseModel):
    status: Literal["submitted"]


# ---------- Results ----------

class Score(BaseModel):
    """Reused for the overall score and for each section."""
    correct: int
    total: int
    percent: float


class ReviewItem(PublicQuestion):
    """A question after submission: the public fields plus the reveal."""
    your_answer: Letter | None
    correct_answer: Letter
    is_correct: bool
    explanation: str


class ResultsResponse(BaseModel):
    attempt_id: str
    submitted_at: datetime
    time_taken_seconds: int
    overall: Score
    sections: dict[Section, Score]
    review: list[ReviewItem]