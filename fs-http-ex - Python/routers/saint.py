from fastapi import APIRouter, Query
from database import connect_to_database
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json

router = APIRouter()

db_connection = connect_to_database()
db_cursor = db_connection.cursor(dictionary=True)


with open('./files/customers.json', 'r') as file:
    customers_data = json.load(file)

class Occupation(BaseModel):
    id: int
    name: str
    isSaint: bool

class Saint(BaseModel):
    id: int
    name: str
    age: int
    occupation: Occupation
    password: str
    is_admin: bool
    image_path: str


@router.get("/json")
async def get_json():
    return customers_data






@router.post("/saints/")
async def create_saint(saint: Saint):
    # Check if the occupation already exists in the database
    db_cursor.execute("SELECT * FROM Occupation WHERE id = %s", (saint.occupation.id,))
    existing_occupation = db_cursor.fetchone()
    if not existing_occupation:
        # If the occupation doesn't exist, insert it into the database
        db_cursor.execute("INSERT INTO Occupation (id, name, isSaint) VALUES (%s, %s, %s)", (saint.occupation.id, saint.occupation.name, saint.occupation.isSaint))
        db_connection.commit()

    # Insert the saint into the Saint table
    insert_query = "INSERT INTO Saint (id, name, age, occupation_id,password,is_admin) VALUES (%s, %s, %s, %s,%s,%s,%s)"
    db_cursor.execute(insert_query, (saint.id, saint.name, saint.age, saint.occupation.id,saint.password,saint.is_admin,saint.image_path))
    db_connection.commit()
    return saint

@router.get("/saints")
async def get_saints(is_Saint: bool = Query(True, description="Filter by saints")):
    if is_Saint:
        saints = [customer for customer in customers_data if customer['occupation']['isSaint']]
        return saints
    else:
        non_saints = [customer for customer in customers_data if not customer['occupation']['isSaint']]
        return non_saints

@router.get("/customers", response_class=HTMLResponse)
async def display_customers():
    # Fetch all saints from the database along with their associated occupation names and image paths
    db_cursor.execute("""
        SELECT saint.id, saint.name AS saint_name, saint.age, saint.password, saint.is_admin, Occupation.name AS occupation_name, saint.image_path
        FROM saint
        INNER JOIN Occupation ON saint.occupation_id = Occupation.id
    """)
    saints = db_cursor.fetchall()

    table_content = ""
    for saint in saints:
        link = f"<a href='/who?id={saint['id']}'>{saint['saint_name']}</a>"
        image_tag = f"<img src='{saint['image_path']}' alt='{saint['saint_name']}'>"
        table_content += f"<tr><td>{link}</td><td>{saint['age']}</td><td>{saint['occupation_name']}</td><td>{saint['password']}</td><td>{'Admin' if saint['is_admin'] else 'Not Admin'}</td><td>{image_tag}</td></tr>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Saints</title>
    </head>
    <body>
        <h1>Saints</h1>
        <table border="1">
            <tr>
                <th>Name</th>
                <th>Age</th>
                <th>Occupation</th>
                <th>Password</th>
                <th>Admin</th>
                <th>Image</th>
            </tr>
            {table_content}
        </table>
    </body>
    </html>
    """
    return html_content

@router.get("/who")
async def get_saint(id: int = Query(..., description="Saint ID")):
    # Fetch the saint details from the database based on the provided ID
    db_cursor.execute("""
        SELECT saint.id, saint.name AS saint_name, saint.age, saint.password, saint.is_admin, Occupation.name AS occupation_name
        FROM saint
        INNER JOIN Occupation ON saint.occupation_id = Occupation.id
        WHERE saint.id = %s
    """, (id,))
    saint = db_cursor.fetchone()
    if saint:
        return saint
    else:
        return "No such saint"
