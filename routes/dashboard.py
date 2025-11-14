# routes/dashboard.py
from fastapi import APIRouter

router = APIRouter(tags=["Dashboard"])

@router.get("/dashboard/summary")
def dashboard_summary():
    # mock; replace later with DB logic
    return {
        "capital": {
            "snap_date": "2025-10-31",
            "nav_usd": 125000.50,
            "pnl_daily_usd": 487.20,
        }
    }
