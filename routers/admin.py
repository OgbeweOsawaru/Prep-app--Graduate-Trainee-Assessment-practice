from datetime import datetime, timedelta, timezone
from typing import Optional
from models import Attempt as AttemptModel, AttemptQuestion,Answer,SeenQuestions
from fastapi import APIRouter, HTTPException,Depends,status
from sqlalchemy.orm import Session
from sqlalchemy import select,func
from models import User,Attempt
from database import get_db
import config
from attempt import Attempt, create_attempt, get_attempt
from bank import load_bank
from grader import grade
from schemas import RegisterRequest,UserResponse,LoginRequest,TokenResponse
from security import ADMIN_KEY
from fastapi import Header

def require_admin(x_admin_key: str | None = Header(default=None)):
    if ADMIN_KEY is None or x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Admin only")
"""Find one user by email or id
See one user’s attempts, with a count
Delete a user’s attempts, for example to reset their free tests"""
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
@router.get("/get_users",response_model=list[UserResponse])
def full_view(db: Session = Depends(get_db)):
    users = db.scalars(
    select(User)
    ).all()     
   
    return users

@router.get("/find_user",response_model=UserResponse)
def find_by_email(email:str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=404,detail="Email not found")
    return user

     
@router.get("/find_user_id",response_model=UserResponse)
def find_by_id(id:int, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.id == id))
    if not user:
        raise HTTPException(status_code=404,detail="id not found")
    return user
@router.get("/user_attempts")
def find_user_attempts(email:str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=404,detail="Email not found")
    total = db.scalar(
    select(func.count())
    .select_from(AttemptModel)
    .where(AttemptModel.user_id == user.id)
)
    return user.email,total
@router.delete("/reset_attempts")
def reset_user_attempts(email:str, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code=404,detail="Email not found")
    for i in user.user_attempts:
        db.delete(i)
    total = db.scalar(
        select(func.count())
        .select_from(AttemptModel)
        .where(AttemptModel.user_id == user.id)
    )
    db.commit()
    return total
@router.delete("/reset_seen")
def reset_user_seen(id:int, db: Session = Depends(get_db)):
    user_seen = db.scalars(select(SeenQuestions).where(SeenQuestions.user_id == id)).all()
    if not user_seen:
        raise HTTPException(status_code=404,detail="No seens found")
    for i in user_seen:    
        db.delete(i)
    db.commit()
    
