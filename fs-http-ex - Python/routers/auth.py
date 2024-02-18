from fastapi import APIRouter, Response,Cookie
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from database import connect_to_database
from exceptions import CustomHTTPException
import secrets

router = APIRouter()

db_connection = connect_to_database()
db_cursor = db_connection.cursor(dictionary=True)

active_session_tokens = set()

class Login(BaseModel):
    username: str
    password: str


def validate_session_token(session_token: Optional[str] = Cookie(None)):
    if session_token is None:
        raise CustomHTTPException(status_code=401, detail={
            "status": 401,
            "message": "Unauthorized",
            "date": datetime.now().isoformat()
        })
    if session_token not in active_session_tokens:
        raise CustomHTTPException(status_code=401, detail={
            "status": 401,
            "message": "Invalid session token",
            "date": datetime.now().isoformat()
        })
    return True


@router.post("/login")
async def login(login: Login, response: Response):
    query = "SELECT * FROM Saint WHERE name = %s AND password = %s AND is_admin = 1"
    db_cursor.execute(query, (login.username, login.password))
    user = db_cursor.fetchone()
    if user:
        session_token = secrets.token_urlsafe(32)
        response.set_cookie(key="session_token", value=session_token, httponly=True, samesite="strict")
        active_session_tokens.add(session_token)
        return {"message": "Login successful"}
    else:
        raise CustomHTTPException(status_code=401, detail={
            "status": 401,
            "message": "Invalid credentials",
            "date": datetime.now().isoformat()
        })
