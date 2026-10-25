import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "8"))


def enabled() -> bool:
    return bool(os.getenv("GROQ_API_KEY")) and os.getenv("LIGHTCONE_OFFLINE") != "1"


def chat_json(system: str, user: str) -> dict:
    response = httpx.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
        json={
            "model": MODEL,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=TIMEOUT_S,
    )
    response.raise_for_status()
    return json.loads(response.json()["choices"][0]["message"]["content"])
