# routes/intelligence.py
import os, httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

class Ask(BaseModel):
    prompt: str

@router.get("/ping")
def ping():
    return {"ok": True, "env_has_key": bool(os.getenv("OPENAI_API_KEY"))}

# Safe/robust version: handles missing key, timeouts, bad model, etc.
@router.post("")
def intelligence(req: Ask):
    if not os.getenv("OPENAI_API_KEY"):
        # Don’t hang if key missing
        return {"reply": "⚠️ OPENAI_API_KEY not set on server. Set it and try again."}

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        # Add a network timeout so it never hangs forever
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # reliable, light
            messages=[{"role":"user","content": req.prompt}],
            timeout=15,           # seconds
        )
        return {"reply": completion.choices[0].message.content}
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="OpenAI timed out (15s). Check internet/firewall and try again.")
    except Exception as e:
        # Bubble useful error back to UI instead of hanging
        raise HTTPException(status_code=500, detail=str(e))
from fastapi import APIRouter
from openai import OpenAI
import os

router = APIRouter(prefix="/intelligence")

@router.post("/")
def intelligence(prompt: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return {"reply": completion.choices[0].message.content}
