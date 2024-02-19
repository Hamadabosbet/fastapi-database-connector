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
    insert_query = "INSERT INTO Saint (id, name, age, occupation_id,password,is_admin) VALUES (%s, %s, %s, %s,%s,%s)"
    db_cursor.execute(insert_query, (saint.id, saint.name, saint.age, saint.occupation.id,saint.password,saint.is_admin))
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
    table_content = ""
    for customer in customers_data:
        link = f"<a href='/who?id={customer['id']}'>{customer['name']}</a>"
        table_content += f"<tr><td>{link}</td><td>{customer['age']}</td><td>{customer['occupation']['name']}</td></tr>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Customers</title>
    </head>
    <body>
        <h1>Customers</h1>
        <table border="1">
            <tr>
                <th>Name</th>
                <th>Age</th>
                <th>Occupation</th>
            </tr>
            {table_content}
        </table>
    </body>
    </html>
    """
    return html_content

@router.get("/who")
async def get_customer(id: int = Query(..., description="Customer ID")):
    for customer in customers_data:
        if customer['id'] == id:
            return customer
    return "No such customer"
