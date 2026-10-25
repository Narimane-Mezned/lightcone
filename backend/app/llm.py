import hashlib
import json
import os
import re
import threading
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
MODELS = [m.strip() for m in os.getenv(
    "LLM_MODELS",
    "meta-llama/llama-3.3-70b-instruct:free,openai/gpt-oss-120b:free",
).split(",") if m.strip()]
MODEL = MODELS[0] if MODELS else "none"
TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "20"))
CACHE_FILE = ROOT / ".cache" / "llm_cache.json"
_lock = threading.Lock()


def _key() -> str:
    return os.getenv("OPENROUTER_API_KEY", "")


def enabled() -> bool:
    return bool(_key()) and bool(MODELS) and os.getenv("LIGHTCONE_OFFLINE") != "1"


def _load_cache() -> dict:
    try:
        return json.loads(CACHE_FILE.read_text())
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE_FILE.parent.mkdir(exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache, indent=1))
    except Exception:
        pass


def _extract_json(content: str) -> dict:
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def _call(model: str, system: str, user: str, json_mode: bool) -> dict:
    body = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    response = httpx.post(
        BASE_URL,
        headers={
            "Authorization": f"Bearer {_key()}",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "Lightcone",
        },
        json=body,
        timeout=TIMEOUT_S,
    )
    response.raise_for_status()
    return _extract_json(response.json()["choices"][0]["message"]["content"])


def chat_json(system: str, user: str) -> tuple[dict, str]:
    cache_key = hashlib.sha256((system + "\x00" + user).encode()).hexdigest()
    with _lock:
        cache = _load_cache()
        if cache_key in cache:
            hit = cache[cache_key]
            return hit["data"], hit["model"]
    last_error: Exception | None = None
    for model in MODELS:
        for json_mode in (True, False):
            try:
                data = _call(model, system, user, json_mode)
            except httpx.HTTPStatusError as error:
                last_error = error
                if error.response.status_code == 400 and json_mode:
                    continue
                break
            except Exception as error:
                last_error = error
                break
            with _lock:
                cache = _load_cache()
                cache[cache_key] = {"data": data, "model": model}
                _save_cache(cache)
            return data, model
    raise last_error or RuntimeError("no model configured")
