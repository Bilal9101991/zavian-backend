# routes/intelligence.py
import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

# 1) Define the request model FIRST
class Ask(BaseModel):
    prompt: str

# 2) Simple health check (no OpenAI)
@router.get("/ping")
def ping():
    return {"ok": True, "env_has_key": bool(os.getenv("OPENAI_API_KEY"))}

# 3) Echo endpoint (no OpenAI) to confirm FastAPI is responsive
@router.post("/echo")
def echo(req: Ask):
    return {"reply": f"ECHO: {req.prompt}"}

# 4) Real OpenAI endpoint (with timeout + clear errors)
@router.post("")
def intelligence(req: Ask):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return {"reply": "⚠️ OPENAI_API_KEY is not set on the server. Set it and restart."}

    client = OpenAI(api_key=key)
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": req.prompt}],
            timeout=12,  # seconds
        )
        return {"reply": completion.choices[0].message.content}
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="OpenAI timed out (12s). Check internet/firewall and try again.")
    except httpx.ConnectError:
        raise HTTPException(status_code=502, detail="Cannot reach OpenAI. Network or DNS blocked.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
