from dotenv import load_dotenv
load_dotenv()
# main.py
import os, json
from datetime import date
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row

# ---------- App ----------
app = FastAPI(title="Zavian API")

# ---------- CORS ----------
# Use your exact frontend origin. Locally it's http://localhost:3000
# In production, set FRONTEND_URL to your Vercel URL, e.g. https://zavian-frontend.vercel.app
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],   # no "*" when allow_credentials=True
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- DB Config ----------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "zavian")
DB_USER = os.getenv("DB_USER", "zavian")
DB_PASS = os.getenv("DB_PASS", "zavian123")
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")   # Neon/Render need "require"

DB_DSN = (
    f"dbname={DB_NAME} user={DB_USER} password={DB_PASS} "
    f"host={DB_HOST} port={DB_PORT} sslmode={DB_SSLMODE}"
)

# ---------- Ensure tables ----------
def ensure_capital_table():
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS capital_daily(
          snap_date date PRIMARY KEY,
          nav_usd numeric(14,2) NOT NULL,
          pnl_daily_usd numeric(14,2) NOT NULL,
          created_at timestamptz DEFAULT now()
        );
        """)

def ensure_approvals_table():
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS approvals(
          id BIGSERIAL PRIMARY KEY,
          kind text NOT NULL,
          entity_code text,
          payload jsonb NOT NULL,
          status text NOT NULL DEFAULT 'pending',
          created_at timestamptz DEFAULT now(),
          decided_at timestamptz
        );
        """)

def ensure_aurigen_tables():
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS aurigen_projects(
          id BIGSERIAL PRIMARY KEY,
          code text UNIQUE NOT NULL,
          name text NOT NULL,
          budget_usd numeric(12,2) DEFAULT 0,
          spent_usd numeric(12,2) DEFAULT 0,
          progress_pct numeric(5,2) DEFAULT 0,
          stage text DEFAULT 'Concept',
          created_at timestamptz DEFAULT now()
        );
        """)

# ---------- Models ----------
class CapitalSnapshot(BaseModel):
    snap_date: date
    nav_usd: float
    pnl_daily_usd: float

class ApprovalIn(BaseModel):
    kind: str
    entity_code: Optional[str] = None
    payload: dict

class DecisionIn(BaseModel):
    decision: str  # "approve" or "decline"
    comment: Optional[str] = None

class ProjectIn(BaseModel):
    code: str
    name: str
    budget_usd: float
    spent_usd: float = 0
    progress_pct: float = 0
    stage: str = "Concept"

# ---------- Health ----------
@app.get("/")
def home():
    return {"message": "Zavian backend is running successfully 🚀"}

@app.get("/db/ping")
def db_ping():
    with psycopg.connect(DB_DSN) as _:
        return {"ok": True}

# ---------- Capital ----------
@app.post("/ingest/capital/daily-snapshot")
def ingest_capital(s: CapitalSnapshot):
    ensure_capital_table()
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
        INSERT INTO capital_daily(snap_date, nav_usd, pnl_daily_usd)
        VALUES (%s,%s,%s)
        ON CONFLICT (snap_date) DO UPDATE SET
          nav_usd=EXCLUDED.nav_usd,
          pnl_daily_usd=EXCLUDED.pnl_daily_usd;
        """, (s.snap_date, s.nav_usd, s.pnl_daily_usd))
        return {"ok": True}

@app.get("/dashboard/summary")
def dashboard_summary():
    ensure_capital_table()
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT snap_date, nav_usd, pnl_daily_usd
            FROM capital_daily ORDER BY snap_date DESC LIMIT 1;
        """)
        return {"capital": cur.fetchone()}

# ---------- Approvals ----------
@app.post("/approvals")
def create_approval(a: ApprovalIn):
    ensure_approvals_table()
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
        INSERT INTO approvals(kind, entity_code, payload)
        VALUES (%s,%s,%s) RETURNING id;
        """, (a.kind, a.entity_code, json.dumps(a.payload)))
        return {"ok": True, "id": cur.fetchone()["id"]}

@app.get("/approvals")
def list_approvals(status: str = Query("pending")):
    ensure_approvals_table()
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
        SELECT id, kind, entity_code, payload, status, created_at, decided_at
        FROM approvals
        WHERE status = %s
        ORDER BY created_at DESC;
        """, (status,))
        return {"approvals": cur.fetchall()}

@app.post("/approvals/{approval_id}/decision")
def decide_approval(approval_id: int, d: DecisionIn):
    ensure_approvals_table()
    new_status = "approved" if d.decision.lower() == "approve" else "declined"
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
        UPDATE approvals
        SET status=%s, decided_at=now()
        WHERE id=%s;
        """, (new_status, approval_id))
        return {"ok": True, "status": new_status}

# ---------- Aurigen ----------
@app.post("/aurigen/project")
def add_project(p: ProjectIn):
    ensure_aurigen_tables()
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
        INSERT INTO aurigen_projects(code, name, budget_usd, spent_usd, progress_pct, stage)
        VALUES (%s,%s,%s,%s,%s,%s)
        ON CONFLICT (code) DO UPDATE SET
          name=EXCLUDED.name,
          budget_usd=EXCLUDED.budget_usd,
          spent_usd=EXCLUDED.spent_usd,
          progress_pct=EXCLUDED.progress_pct,
          stage=EXCLUDED.stage
        RETURNING id;
        """,
        (p.code, p.name, p.budget_usd, p.spent_usd, p.progress_pct, p.stage))
        return {"ok": True, "id": cur.fetchone()["id"]}

@app.get("/aurigen/summary")
def aurigen_summary():
    ensure_aurigen_tables()
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
        SELECT
          COUNT(*) AS total_projects,
          COALESCE(ROUND(SUM(budget_usd)::numeric,2),0) AS total_budget,
          COALESCE(ROUND(SUM(spent_usd)::numeric,2),0) AS total_spent,
          COALESCE(ROUND(AVG(progress_pct)::numeric,1),0) AS avg_progress
        FROM aurigen_projects;
        """)
        return {"aurigen": cur.fetchone()}

@app.get("/aurigen/projects")
def aurigen_projects():
    ensure_aurigen_tables()
    with psycopg.connect(DB_DSN, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute("""
        SELECT code, name, budget_usd, spent_usd, progress_pct, stage
        FROM aurigen_projects ORDER BY created_at DESC;
        """)
        return {"projects": cur.fetchall()}
from routes.intelligence import router as intelligence_router
app.include_router(intelligence_router)
git init
git add .
git commit -m "chore: initial backend with /intelligence route"

# replace with your real GitHub user/org name:
git remote add origin https://github.com/Bilal9101991/zavian-api.git

git branch -M main
git push -u origin main
# main.py
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Zavian API")

@app.get("/")
def home():
    return {"message": "Zavian backend is running successfully 🚀"}

# If you DIDN'T install swagger-ui-bundle, keep default docs (no extra code).

# Mount the intelligence routes
from routes.intelligence import router as intelligence_router
app.include_router(intelligence_router)
