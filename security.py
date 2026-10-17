import os
from datetime import datetime, timedelta, timezone

import jwt

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
ADMIN_KEY = os.getenv("ADMIN_KEY")
from pwdlib import PasswordHash
# Create a PasswordHash instance with recommended settings
ph = PasswordHash.recommended()
def hash_password(password:str)->str:
    return ph.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks a login attempt's password against the stored hash."""
    return ph.verify(plain_password, hashed_password)

def create_access_token(user_id:int):
    time =datetime.now(timezone.utc)+timedelta(hours=8)
    token={"sub":str(user_id),
           "exp": time }
    return jwt.encode(token, SECRET_KEY,algorithm="HS256")

def decode_access_token(token:str):
    try:
        decoded=jwt.decode(token, SECRET_KEY,algorithms=["HS256"])
        return int(decoded.get("sub"))
    except (jwt.PyJWTError, TypeError,ValueError):
        return None
if __name__ == "__main__":
    token = create_access_token(1)
    print(jwt.decode(token, SECRET_KEY, algorithms=["HS256"]) )    
    print(decode_access_token("garbage"))
    password=input("Give me a password")
    a=hash_password(password)
    verify=input()
    print(verify_password(verify,a))
