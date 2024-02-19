from fastapi import APIRouter, Depends, Path
from datetime import datetime
from database import connect_to_database
from .auth import validate_session_token
from exceptions import CustomHTTPException 


router = APIRouter()

db_connection = connect_to_database()
db_cursor = db_connection.cursor(dictionary=True)




@router.get("/admin/saint/age/{min_age}/{max_age}", dependencies=[Depends(validate_session_token)])
async def saints_in_age_range(min_age: int = Path(..., title="Minimum Age", ge=0), max_age: int = Path(..., title="Maximum Age", ge=0)):
    if min_age >= max_age:
        raise CustomHTTPException(status_code=400, detail={
            "status": 400,
            "message": "Minimum age must be less than maximum age",
            "date": datetime.now().isoformat()
        })
    
    db_cursor.execute("SELECT * FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = true) AND age BETWEEN %s AND %s", (min_age, max_age))
    saints = db_cursor.fetchall()
    return saints

@router.get("/admin/notsaint/age/{min_age}/{max_age}", dependencies=[Depends(validate_session_token)])
async def not_saints_in_age_range(min_age: int = Path(..., title="Minimum Age", ge=0), max_age: int = Path(..., title="Maximum Age", ge=0)):
    if min_age >= max_age:
        raise CustomHTTPException(status_code=400, detail={
            "status": 400,
            "message": "Minimum age must be less than maximum age",
            "date": datetime.now().isoformat()
        })
    
    db_cursor.execute("SELECT * FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = false) AND age BETWEEN %s AND %s", (min_age, max_age))
    not_saints = db_cursor.fetchall()
    return not_saints

@router.get("/admin/name/{name}", dependencies=[Depends(validate_session_token)])
async def saints_with_name(name: str = Path(..., title="Name", min_length=2, max_length=11, pattern="^[a-zA-Z]+$")):
    db_cursor.execute("SELECT * FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = true) AND name LIKE %s", ('%' + name + '%',))
    saints = db_cursor.fetchall()
    return saints

@router.get("/admin/average", dependencies=[Depends(validate_session_token)])
async def average_ages():
    saint_avg_query = "SELECT AVG(age) AS saint_avg FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = true)"
    not_saint_avg_query = "SELECT AVG(age) AS not_saint_avg FROM Saint WHERE occupation_id IN (SELECT id FROM Occupation WHERE isSaint = false)"
    db_cursor.execute(saint_avg_query)
    saint_avg = db_cursor.fetchone()['saint_avg']
    db_cursor.execute(not_saint_avg_query)
    not_saint_avg = db_cursor.fetchone()['not_saint_avg']
    return {"saint_average_age": saint_avg, "not_saint_average_age": not_saint_avg}
