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
    """Confirms route is live and whether the server sees OPENAI_API_KEY."""
    return {"ok": True, "env_has_key": bool(os.getenv("OPENAI_API_KEY"))}

@router.post("/echo")
def echo(req: Ask):
    return {"reply": f"ECHO: {req.prompt}"}

@router.post("")
def intelligence(req: Ask):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY missing on server")

    client = OpenAI(api_key=key)

    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",  # broadly available; change if you prefer
            messages=[{"role": "user", "content": req.prompt}],
            temperature=0.7,
            timeout=15,
        )
        return {"reply": resp.choices[0].message.content}
    except Exception as e:
        # Bubble up the real reason so we can see it from the client/logs
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
