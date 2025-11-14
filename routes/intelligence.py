from fastapi import APIRouter

router = APIRouter(tags=["Intelligence"])

@router.get("/kpis", summary="KPIs")
def get_kpis():
    return {
        "nav_usd": 125000.0,
        "pnl_daily_usd": 730.5,
        "signals_active": 4,
        "rd_projects": 3,
    }
