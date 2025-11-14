# routes/approvals.py
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Approvals"])

# simple in-memory store (mock)
PENDING = [
    {"id": 1, "kind": "SKU_CREATE", "entity_code": "DEC-HENNA-100", "payload": {"title": "Decent Henna 100g"}},
    {"id": 2, "kind": "BUDGET", "entity_code": "AUR-2025-Q4", "payload": {"amount": 2500}},
]

class DecisionBody(BaseModel):
    decision: str   # "approve" | "decline"
    comment: str | None = None

@router.get("/approvals")
def list_approvals(status: str = Query("pending")):
    if status != "pending":
        return {"approvals": []}
    return {"approvals": PENDING}

@router.post("/approvals/{approval_id}/decision")
def decide(approval_id: int, body: DecisionBody):
    # remove from mock list when decided
    idx = next((i for i, a in enumerate(PENDING) if a["id"] == approval_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    decided = PENDING.pop(idx)
    decided["decision"] = body.decision
    decided["comment"] = body.comment
    return {"ok": True, "approval": decided}
