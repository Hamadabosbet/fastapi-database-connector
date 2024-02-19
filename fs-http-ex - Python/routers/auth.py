from fastapi import APIRouter, Response,Cookie
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from database import connect_to_database
from exceptions import CustomHTTPException
import secrets
from cryptography.fernet import Fernet

router = APIRouter()


db_connection = connect_to_database()
db_cursor = db_connection.cursor(dictionary=True)

encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)
active_session_tokens = set()

class Login(BaseModel):
    username: str
    password: str

@router.get("/")
async def index():
    return "Ahalan! You can fetch some json by navigating to '/json'"

def validate_session_token(session_token: Optional[str] = Cookie(None)):
    if session_token is None:
        raise CustomHTTPException(status_code=401, detail={
            "status": 401,
            "message": "Unauthorized",
            "date": datetime.now().isoformat()
        })

    # Decrypt the session token
    decrypted_token = cipher_suite.decrypt(session_token.encode())
    user_id = decrypted_token.decode().split("-")[-1]
    
    # Retrieve user information from the database
    query = "SELECT * FROM Saint WHERE id = %s"
    db_cursor.execute(query, (user_id,))
    user = db_cursor.fetchone()
    
    if not user:
        raise CustomHTTPException(status_code=401, detail={
            "status": 401,
            "message": "User not found",
            "date": datetime.now().isoformat()
        })

    # Check if the user is an admin
    if user.get('is_admin') != 1:
        raise CustomHTTPException(status_code=403, detail={
            "status": 403,
            "message": "Forbidden: User is not an admin",
            "date": datetime.now().isoformat()
        })

    return True


@router.post("/login")
async def login(login: Login, response: Response):
    query = "SELECT * FROM Saint WHERE name = %s AND password = %s"
    db_cursor.execute(query, (login.username, login.password))
    user = db_cursor.fetchone()
    if user:
        session_token = secrets.token_urlsafe(32)
        # Append user ID for uniqueness
        session_token_with_id = f"{session_token}-{user['id']}"
        # Encrypt the session token
        encrypted_token = cipher_suite.encrypt(session_token_with_id.encode()).decode()
        response.set_cookie(key="session_token", value=encrypted_token, httponly=True, samesite="strict")
        encrypted_password = cipher_suite.encrypt(user['password'].encode())
        response.set_cookie(key="password", value=encrypted_password, httponly=True, samesite="strict")
        active_session_tokens.add(session_token_with_id)
        return {"message": "Login successful"}
    else:
        raise CustomHTTPException(status_code=401, detail={
            "status": 401,
            "message": "Invalid credentials",
            "date": datetime.now().isoformat()
        })
