from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routers import auth, saint, admin,fileUpload 
from exceptions import CustomHTTPException

app = FastAPI()

@app.exception_handler(CustomHTTPException)
async def custom_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)

app.include_router(fileUpload.router)
app.include_router(auth.router)
app.include_router(saint.router)
app.include_router(admin.router)
