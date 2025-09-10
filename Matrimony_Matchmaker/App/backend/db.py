import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="kushal",
        database="matrimony_db",
        port=3306
    )
