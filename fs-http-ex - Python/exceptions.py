from fastapi import HTTPException
from datetime import datetime

class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int = 400, detail: dict = None):
        self.status_code = status_code
        self.detail = detail or {
            "status": status_code,
            "message": "An error occurred",
            "date": datetime.now().isoformat()
        }
        super().__init__(status_code=status_code, detail=self.detail)
