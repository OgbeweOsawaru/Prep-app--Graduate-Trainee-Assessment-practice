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
sections={"C":"Critical","V":"Verbal","N":"Numerical"}
def get_progress( user_id,db):
    bank=load_bank()
    attempt_answers={}
    user=db.scalar(select(User).where(User.id==user_id))
    chosen_op={}
    meta={}
    for i in user.user_attempts:
        if i.submitted_at is None:
            continue
        answers={}
        rows = db.execute(select(Answer.question_id, Answer.chosen).where(Answer.attempt_id == i.id)).all()
        for question in i.questions:
            for line in bank:
                if line.id==question.question_id:
                    answers[line.id]=line.answer
        num=int(len(attempt_answers)+1)
        attempt_answers[num]=answers
        chosen_op[num]=rows
        meta[num]=[i.started_at,len(answers)]
    return [attempt_answers,chosen_op,meta]
def get_score( attempt_answers,chosen,meta):
    scoring=[]
    
    per=[]
    for  (k1,v1) in  zip(attempt_answers.keys(),chosen.values()):
        score=0
        for i in v1:
            
            a=attempt_answers[k1]
            if a[i[0]] == i[1]:
                score+=1
        letters = {q[0] for q in attempt_answers[k1]}
        if len(letters) > 1:
            section = "Full Test"
        else:
            section = sections[letters.pop()]
        score_by_section = {
            "section": section,
            "score": score,
            "total": meta[k1][1],
            "date": meta[k1][0],
        }
        per.append(score_by_section)
        scoring.append(score)
    return per

@router.get("/progress")
def progress(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    attempt_answers, chosen,meta = get_progress(current_user.id, db)
    return get_score(attempt_answers, chosen,meta)