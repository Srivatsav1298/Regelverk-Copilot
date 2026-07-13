import os
import psycopg2
# pyrefly: ignore [missing-import
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

if __name__ == "__main__":
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("Database connection OK:", cur.fetchone())
    conn.close()