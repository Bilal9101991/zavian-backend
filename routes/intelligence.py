from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import os

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

class PromptIn(BaseModel):
    prompt: str

@router.get("/ping")
def ping():
    return {"ok": True, "env_has_key": bool(os.getenv("OPENAI_API_KEY"))}

@router.post("/echo")
def echo(p: PromptIn):
    return {"reply": f"ECHO: {p.prompt}"}

@router.post("/")
def run_intelligence(p: PromptIn):
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY environment variable")

        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Jarvis, an intelligent assistant."},
                {"role": "user", "content": p.prompt}
            ]
        )

        return {"reply": completion.choices[0].message.content}

    except Exception as e:
        # Log error for debugging
        return {"error": str(e)}
