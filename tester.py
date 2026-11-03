import httpx
def login_attempt(email, password):
    details= {"email": email,
            "password": password
            }
    r = httpx.post("http://127.0.0.1:8000/auth/login", json=details)
    return r.status_code
for i in range(120):
    print(login_attempt("test@gmail.com", "osawaru"))