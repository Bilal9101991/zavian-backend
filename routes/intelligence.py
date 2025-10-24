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
    return {"ok": True, "env_has_key": bool(os.getenv("OPENAI_API_KEY"))}

@router.post("")
def intelligence(req: Ask):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return {"reply": "⚠️ OPENAI_API_KEY is not set on the server."}

    client = OpenAI(api_key=key)
    try:
        # use a reliable lightweight model
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": req.prompt}],
            timeout=15
        )
        return {"reply": resp.choices[0].message.content}
    except Exception as e:
        # return the actual reason to the client
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
