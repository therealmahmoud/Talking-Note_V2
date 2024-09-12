#!/usr/bin/env python3
import mysql.connector

# Connect to the database
try:
    connection = mysql.connector.connect(
    host='localhost',
    port='3306',
    user='flask_user',
    password='flask_password',
    database='flask_db'
    )

    cursor = connection.cursor()

    # Define the SQL query to create a table
    table = """
    CREATE TABLE IF NOT EXISTS notes(notes_id INT AUTO_INCREMENT PRIMARY KEY NOT NULL,
    title VARCHAR(45) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)"""

    cursor.execute(table)
    print("executed successfully")

    cursor.commit()

except mysql.connector.errors as e:
    print("error while connecting to database", e)


finally:
    if connection.is_connected():
        print('Connected to the database')
