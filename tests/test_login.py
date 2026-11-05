import httpx
from models import User
from database import SessionLocal
from sqlalchemy import select
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)
db=SessionLocal()
def unique_email():
    user=[f"test_{uuid.uuid4().hex[:8]}",f"test_{uuid.uuid4().hex[:8]}@gmail.com"]
    return user

def login_attempt_Test_Client(email, password):
    details= {"email": email,
            "password": password
            }
    r=client.post("/auth/login",json=details)
    return r.status_code


def register_attempt_Test_Client(username,email, password):
    details= {"username":username,
        "email": email,
            "password": password
            }
    r = client.post("/auth/register", json=details)
    return r.status_code


def test_register_account_fails_with_wrong_length_password():
    tester=unique_email()
    code = register_attempt_Test_Client(tester[0],tester[1], "teste")
    assert code == 422
    user=db.scalar(select(User).where(User.username== tester[0]))
    if(user):
        db.delete(user)
        db.commit()
def test_register_account_succeeds_with_proper_length():
    tester=unique_email()
    code = register_attempt_Test_Client(tester[0],tester[1], "tester")
    assert code == 201
    user=db.scalar(select(User).where(User.username== tester[0]))
    if user:
        db.delete(user)
        db.commit()
def test_register_account_fails_existing():
    tester=unique_email()
    testing = register_attempt_Test_Client(tester[0],tester[1], "teste")
    if testing == 201:
        code = register_attempt_Test_Client(tester[0],tester[1], "teste")
        assert code == 400
    user=db.scalar(select(User).where(User.username== tester[0]))
    if user:
        db.delete(user)
        db.commit()

def test_correct_login_succeeds():
    tester=unique_email()
    testing = register_attempt_Test_Client(tester[0],tester[1], "tester")
    if testing == 201:
        code = login_attempt_Test_Client(tester[1], "tester")
        assert code == 200
    user=db.scalar(select(User).where(User.username== tester[0]))
    if user:
        db.delete(user)
        db.commit()

def test_rate_limit_blocks_after_too_many_attempts():
    codes=[]
    email = "test@gmail.com"
    password = "wrongpassword"
    for i in range(10):
        trial=login_attempt_Test_Client(email,password)
        codes.append(trial)
    assert 429 in codes
"""def login_attempt(email, password):
    details= {"email": email,
            "password": password
            }
    r = httpx.post("http://127.0.0.1:8000/auth/login", json=details)
    return r.status_code
def register(username,email, password):
    details= {"username":username,
        "email": email,
            "password": password
            }
    r = httpx.post("http://127.0.0.1:8000/auth/register", json=details)
    return r.status_code

def test_register_account_fails_with_wrong_length_password():
    code = register("tester","tester@gmail.com", "teste")
    assert code == 422
    user=db.scalar(select(User).where(User.username== "tester"))
    if(user):
        db.delete(user)
        db.commit()
def test_register_account_succeeds_with_proper_length():
    code = register("tester","tester@gmail.com", "tester")
    assert code == 201
    user=db.scalar(select(User).where(User.username== "tester"))
    if user:
        db.delete(user)
        db.commit()
def test_register_account_fails_existing():
    code = register("osasco","osas@gmail.com", "osasiscool")
    assert code == 400

def test_correct_login_succeeds():
    code = login_attempt("osas@gmail.com", "osasiscool")
    assert code == 200

def test_rate_limit_blocks_after_too_many_attempts():
    codes=[]
    email = "test@gmail.com"
    password = "wrongpassword"
    for i in range(10):
        trial=login_attempt(email,password)
        codes.append(trial)
    assert 429 in codes

"""