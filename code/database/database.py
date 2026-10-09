import sqlite3

DB_PATH = "database/museum.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets you write obj["title"] instead of obj[1]
    return conn
