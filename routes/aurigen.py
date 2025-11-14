# routes/aurigen.py
from fastapi import APIRouter

router = APIRouter(tags=["Aurigen"])

@router.get("/aurigen/summary")
def aurigen_summary():
    return {
        "aurigen": {
            "total_projects": 4,
            "total_budget": 120000,
            "total_spent": 45500,
            "avg_progress": 62,
        }
    }
