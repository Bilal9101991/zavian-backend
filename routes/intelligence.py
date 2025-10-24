# routes/intelligence.py
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

class Ask(BaseModel):
    prompt: str

@router.get("/ping")
def ping():
    """Simple health check."""
    return {"ok": True, "env_has_key": bool(os.getenv("OPENAI_API_KEY"))}

@router.post("")
def intelligence(req: Ask):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY missing on server")

    client = OpenAI(api_key=key)

    try:
        result = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": req.prompt}],
            temperature=0.7,
        )
        return {"reply": result.choices[0].message.content}
    except Exception as e:
        # Return the specific error text so we can see what’s failing
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
