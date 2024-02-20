from fastapi import FastAPI
from fastapi.responses import JSONResponse
from routers import auth, saint, admin,fileUpload 
from routers.fileUpload import UPLOAD_DIRECTORY
from exceptions import CustomHTTPException

from fastapi.staticfiles import StaticFiles
app = FastAPI()

@app.exception_handler(CustomHTTPException)
async def custom_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)

app.mount("/assets", StaticFiles(directory=UPLOAD_DIRECTORY), name="assets")
app.include_router(fileUpload.router)
app.include_router(auth.router)
app.include_router(saint.router)
app.include_router(admin.router)
