import boto3
from fastapi import APIRouter, UploadFile, File, Form, Cookie, Depends
from fastapi.responses import HTMLResponse
from .auth import validate_user_session, get_user_id_from_session_token
from database import connect_to_database

router = APIRouter()


db_connection = connect_to_database()
db_cursor = db_connection.cursor(dictionary=True)

AWS_ACCESS_KEY_ID = "AKIATCKAO3E54RUT3WWQ"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION_NAME = "eu-north-1"
S3_BUCKET_NAME = "file-management-fastapi"

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION_NAME
)


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

    # Save the file to S3
    file_path = await save_uploaded_file_to_s3(file)

    if file_path is None:
        return {"error": "File upload failed"}

    # Insert file path into the database for the user
    query = "UPDATE saint SET image_path = %s WHERE id = %s"
    db_cursor.execute(query, (file_path, user_id))
    db_connection.commit()
    db_connection.close()  # Close the database connection after commit

    return {"file_name": file_name, "file_path": file_path}


async def save_uploaded_file_to_s3(file: UploadFile):
    # Generate a unique filename (use UUID or other method)
    unique_filename = "folder/" + file.filename
    # Upload file to S3 bucket
    try:
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            unique_filename
        )
        file_path = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION_NAME}.amazonaws.com/{unique_filename}"
        return file_path
    except Exception as e:
        print("Error uploading file to S3:", e)
        return None
    