import os
import psycopg2
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from pgvector.psycopg2 import register_vector

load_dotenv()

def get_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    register_vector(conn)   # teaches psycopg2 how to handle the vector type
    return conn

if __name__ == "__main__":
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("Database connection OK:", cur.fetchone())
    conn.close()