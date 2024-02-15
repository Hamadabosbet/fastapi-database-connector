from fastapi import FastAPI, Query, HTTPException, Path
from fastapi.responses import HTMLResponse
import json
from pydantic import BaseModel
import mysql.connector

app = FastAPI()
with open('./files/customers.json', 'r') as file:
    customers_data = json.load(file)


# Connect to MySQL database
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Hamad12345",
    database="saints"
)
db_cursor = db_connection.cursor(dictionary=True)

class Occupation(BaseModel):
    id: int
    name: str
    isSaint: bool

class Saint(BaseModel):
    id: int
    name: str
    age: int
    occupation: Occupation



@app.post("/saints/")
async def create_saint(saint: Saint):
    # Check if the occupation already exists in the database
    db_cursor.execute("SELECT * FROM Occupation WHERE id = %s", (saint.occupation.id,))
    existing_occupation = db_cursor.fetchone()
    if not existing_occupation:
        # If the occupation doesn't exist, insert it into the database
        db_cursor.execute("INSERT INTO Occupation (id, name, isSaint) VALUES (%s, %s, %s)", (saint.occupation.id, saint.occupation.name, saint.occupation.isSaint))
        db_connection.commit()

    # Insert the saint into the Saint table
    insert_query = "INSERT INTO Saint (id, name, age, occupation_id) VALUES (%s, %s, %s, %s)"
    db_cursor.execute(insert_query, (saint.id, saint.name, saint.age, saint.occupation.id))
    db_connection.commit()
    return saint

@app.get("/")
async def index():
    return "Ahalan! You can fetch some json by navigating to '/json'"

@app.get("/json")
async def get_json():
    return customers_data

@app.get("/saints")
async def get_saints(is_Saint: bool = Query(True, description="Filter by saints")):
    if is_Saint:
        saints = [customer for customer in customers_data if customer['occupation']['isSaint']]
        return saints
    else:
        non_saints = [customer for customer in customers_data if not customer['occupation']['isSaint']]
        return non_saints

@app.get("/customers", response_class=HTMLResponse)
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

@app.get("/who")
async def get_customer(id: int = Query(..., description="Customer ID")):
    for customer in customers_data:
        if customer['id'] == id:
            return customer
    return "No such customer"

@app.get("/admin/saint/age/{min_age}/{max_age}")
async def saints_in_age_range(min_age: int = Path(..., title="Minimum Age", ge=0), max_age: int = Path(..., title="Maximum Age", ge=0)):
    if min_age >= max_age:
        raise HTTPException(status_code=400, detail="Minimum age must be less than maximum age.")
    
    db_cursor.execute("SELECT * FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = true) AND age BETWEEN %s AND %s", (min_age, max_age))
    saints = db_cursor.fetchall()
    return saints

@app.get("/admin/notsaint/age/{min_age}/{max_age}")
async def not_saints_in_age_range(min_age: int = Path(..., title="Minimum Age", ge=0), max_age: int = Path(..., title="Maximum Age", ge=0)):
    if min_age >= max_age:
        raise HTTPException(status_code=400, detail="Minimum age must be less than maximum age.")
    
    db_cursor.execute("SELECT * FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = false) AND age BETWEEN %s AND %s", (min_age, max_age))
    not_saints = db_cursor.fetchall()
    return not_saints

@app.get("/admin/name/{name}")
async def saints_with_name(name: str = Path(..., title="Name", min_length=2, max_length=11, pattern="^[a-zA-Z]+$")):
    db_cursor.execute("SELECT * FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = true) AND name LIKE %s", ('%' + name + '%',))
    saints = db_cursor.fetchall()
    return saints

@app.get("/admin/average")
async def average_ages():
    saint_avg_query = "SELECT AVG(age) AS saint_avg FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = true)"
    not_saint_avg_query = "SELECT AVG(age) AS not_saint_avg FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = false)"
    db_cursor.execute(saint_avg_query)
    saint_avg = db_cursor.fetchone()['saint_avg']
    db_cursor.execute(not_saint_avg_query)
    not_saint_avg = db_cursor.fetchone()['not_saint_avg']
    return {"saint_average_age": saint_avg, "not_saint_average_age": not_saint_avg}
