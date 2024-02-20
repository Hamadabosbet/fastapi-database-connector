from fastapi import APIRouter,UploadFile, File,Form,Depends,Cookie
from database import connect_to_database
from fastapi.responses import HTMLResponse
from .auth import validate_user_session,get_user_id_from_session_token
import os
import aiofiles

router = APIRouter()


UPLOAD_DIRECTORY = "assets"

db_connection = connect_to_database()
db_cursor = db_connection.cursor(dictionary=True)




@router.get("/upload", response_class=HTMLResponse, dependencies=[Depends(validate_user_session)])
async def upload_form():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Upload File</title>
    </head>
    <body>
        <h1>Upload File</h1>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <label for="file_name">File Name:</label><br>
            <input type="text" id="file_name" name="file_name"><br>
            <label for="file">Choose File:</label><br>
            <input type="file" id="file" name="file"><br><br>
            <input type="submit" value="Submit">
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.post("/upload", dependencies=[Depends(validate_user_session)])
async def upload_file(session_token: str = Cookie(None), file: UploadFile = File(...), file_name: str = Form(...)):
    # Decrypt the session token to get user_id
    user_id = get_user_id_from_session_token(session_token)

    # Save the file
    file_path = await save_uploaded_file(UPLOAD_DIRECTORY, file)

    # Insert file path into the database for the user
    query = "UPDATE saint SET image_path = %s WHERE id = %s"
    db_cursor.execute(query, (file_path, user_id))
    db_connection.commit()

    return {"file_name": file_name, "file_path": file_path}


async def save_uploaded_file(upload_directory: str, file: UploadFile):
    file_path = os.path.join(upload_directory, file.filename)
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(await file.read())
    return file.filename