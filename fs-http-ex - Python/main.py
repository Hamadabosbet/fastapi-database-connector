from fastapi import FastAPI, Query, HTTPException, Path,Cookie,Depends,Response
from fastapi.responses import HTMLResponse
import json
from pydantic import BaseModel
from database import connect_to_database 
import secrets

app = FastAPI()
with open('./files/customers.json', 'r') as file:
    customers_data = json.load(file)


db_connection = connect_to_database()  # Connect to the database

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
    password: str
    is_admin: bool

class Login(BaseModel):
    username: str
    password: str



def is_admin_logged_in(session_token: str = Cookie(None)):
    if session_token is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True
    



@app.post("/login")
async def login(login: Login, response: Response):
    query = "SELECT * FROM Saint WHERE name = %s AND password = %s AND is_admin = 1"
    db_cursor.execute(query, (login.username, login.password))
    user = db_cursor.fetchone()
    if user:
        session_token = secrets.token_urlsafe(32)
        # Set session cookie upon successful authentication
        response.set_cookie(key="session_token", value=session_token)  # Set your desired session token value
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")






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
    insert_query = "INSERT INTO Saint (id, name, age, occupation_id,password,is_admin) VALUES (%s, %s, %s, %s,%s,%s)"
    db_cursor.execute(insert_query, (saint.id, saint.name, saint.age, saint.occupation.id,saint.password,saint.is_admin))
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

@app.get("/admin/saint/age/{min_age}/{max_age}",dependencies=[Depends(is_admin_logged_in)])
async def saints_in_age_range(min_age: int = Path(..., title="Minimum Age", ge=0), max_age: int = Path(..., title="Maximum Age", ge=0)):
    if min_age >= max_age:
        raise HTTPException(status_code=400, detail="Minimum age must be less than maximum age.")
    
    db_cursor.execute("SELECT * FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = true) AND age BETWEEN %s AND %s", (min_age, max_age))
    saints = db_cursor.fetchall()
    return saints

@app.get("/admin/notsaint/age/{min_age}/{max_age}",dependencies=[Depends(is_admin_logged_in)])
async def not_saints_in_age_range(min_age: int = Path(..., title="Minimum Age", ge=0), max_age: int = Path(..., title="Maximum Age", ge=0)):
    if min_age >= max_age:
        raise HTTPException(status_code=400, detail="Minimum age must be less than maximum age.")
    
    db_cursor.execute("SELECT * FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = false) AND age BETWEEN %s AND %s", (min_age, max_age))
    not_saints = db_cursor.fetchall()
    return not_saints

@app.get("/admin/name/{name}",dependencies=[Depends(is_admin_logged_in)])
async def saints_with_name(name: str = Path(..., title="Name", min_length=2, max_length=11, pattern="^[a-zA-Z]+$")):
    db_cursor.execute("SELECT * FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = true) AND name LIKE %s", ('%' + name + '%',))
    saints = db_cursor.fetchall()
    return saints

@app.get("/admin/average",dependencies=[Depends(is_admin_logged_in)])
async def average_ages():
    saint_avg_query = "SELECT AVG(age) AS saint_avg FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = true)"
    not_saint_avg_query = "SELECT AVG(age) AS not_saint_avg FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = false)"
    db_cursor.execute(saint_avg_query)
    saint_avg = db_cursor.fetchone()['saint_avg']
    db_cursor.execute(not_saint_avg_query)
    not_saint_avg = db_cursor.fetchone()['not_saint_avg']
    return {"saint_average_age": saint_avg, "not_saint_average_age": not_saint_avg}
