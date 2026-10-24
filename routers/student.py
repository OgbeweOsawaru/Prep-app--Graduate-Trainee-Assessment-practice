from datetime import datetime, timedelta, timezone
from models import Attempt as AttemptModel, AttemptQuestion,Answer,User
from fastapi import APIRouter, HTTPException,Depends,status
from sqlalchemy.orm import Session
from database import get_db,SessionLocal
import config
from attempt import Attempt, create_attempt, get_attempt
from bank import load_bank,load_questions
from grader import grade
from schemas import ResultsResponse, StartResponse, SubmitRequest, SubmitResponse
from deps import get_current_user
from sqlalchemy import select, func
from bank import load_questions
router = APIRouter(prefix="/student", tags=["student"])

@router.get("/get_attempt_history")
def get_attempt_history(user_id:int, current_user: User = Depends(get_current_user),db: Session = Depends(get_db)):
    questions=load_bank()
    user_attempts=[]
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not allowed",)
    user=select(User).where(User.id==user_id)
    result=db.scalars(user)
    for i in result:
        for k in i.user_attempts:
            user_attempts.append(k.id)
    full_attempt={}
    for num,i in enumerate(user_attempts,start=1):
        statement=select(AttemptModel).where(AttemptModel.id==i)
        result=db.scalars(statement).all()
        question_id=[]
        for attempt in result:
            if attempt.submitted_at is not None:
                for t in attempt.questions:
                    question_id.append(t.question_id)
        print(len(set(question_id)))
        student={}
        for k in questions:
            if k.id in question_id:
                student[k.id]= [k.question,k.answer]
        full_attempt[num]=student

    return (full_attempt)


