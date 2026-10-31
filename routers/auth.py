from datetime import datetime, timedelta, timezone
from models import Attempt as AttemptModel, AttemptQuestion,Answer
from fastapi import APIRouter, HTTPException,Depends,status
from sqlalchemy.orm import Session
from sqlalchemy import select,func
from models import User
from database import get_db
import config
from attempt import Attempt, create_attempt, get_attempt
from bank import load_bank
from grader import grade
from schemas import RegisterRequest,UserResponse,LoginRequest,TokenResponse
from security import hash_password,verify_password,create_access_token
from deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
@router.post("/register", response_model=UserResponse, status_code=201)
def register(user:RegisterRequest,db: Session = Depends(get_db)):
    result= db.execute(
            select(User). where(User.username==user.username),
        )
    existing_user=result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists",)
    
    result= db.execute(
        select(User). where(User.email==user.email),
        )
    existing_email=result.scalars().first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists",)

    new_user=User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
def Login(user:LoginRequest,db: Session = Depends(get_db)):
    result= db.execute(
            select(User). where(func.lower(User.email)==user.email.lower()),
        )
    db_user=result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect Email or Password",)
    if verify_password(user.password,db_user.password_hash):
        return TokenResponse(access_token=create_access_token(db_user.id))
    else: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect Email or Password",)
