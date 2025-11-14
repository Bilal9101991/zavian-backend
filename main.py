from fastapi import FastAPI
import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

app = FastAPI(title="Zavian API")

DATABASE_URL = os.getenv("DATABASE_URL")

@app.get("/")
def home():
    return {"message": "Zavian backend is running 🚀"}

@app.get("/status")
def status():
    return {"status": "ok", "env": os.getenv("ENVIRONMENT", "local")}

@app.get("/db/ping")
def db_ping():
    try:
        if not DATABASE_URL:
            return {"ok": False, "error": "DATABASE_URL is not set"}

        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 AS ok;")
            row = cur.fetchone()
            return {"ok": True, "db": row}
    except Exception as e:
        return {"ok": False, "error": str(e)}
