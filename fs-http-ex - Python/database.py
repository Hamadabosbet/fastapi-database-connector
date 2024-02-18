import mysql.connector

def connect_to_database():
    db_connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Hamad12345",
        database="saints"
    )
    return db_connection