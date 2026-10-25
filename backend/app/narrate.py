import re
import threading

from . import llm

SYSTEM = """You write the decision letter that Lightcone sends to every requester after a "true tie":
two cargo bookings made on Earth and Mars so close in time that, because of light delay,
neither side could have known about the other. Nobody could negotiate in time, so Lightcone decided.

You receive the facts as JSON. Write 3 to 4 short sentences in plain, warm, professional English:
1. Why this was a true tie (the light delay).
2. What each requester receives now and, if any, what is guaranteed on the next ship.
3. Why this is fairer than a random lottery (refer to the lottery outcome given).

Strict rules: use ONLY numbers that appear in the JSON. Do not invent quantities, times or names.
Return ONLY a JSON object: {"narrative": "..."}
"""

_cache: dict[tuple, dict] = {}
_pending: set[tuple] = set()
_lock = threading.Lock()


def _normalise(n: str) -> str:
    if "." in n:
        n = n.rstrip("0").rstrip(".")
    return n.lstrip("0") or "0"


def guardrail_ok(narrative: str, facts_text: str) -> bool:
    allowed = {_normalise(n) for n in re.findall(r"\d+(?:\.\d+)?", facts_text)}
    used = {_normalise(n) for n in re.findall(r"\d+(?:\.\d+)?", narrative)}
    return used <= allowed and 0 < len(narrative) < 900


def _work(key: tuple, facts_text: str) -> None:
    try:
        raw = llm.chat_json(SYSTEM, facts_text)
        narrative = str(raw.get("narrative", "")).strip()
        if guardrail_ok(narrative, facts_text):
            result = {"narrative": narrative, "source": "llm"}
        else:
            result = None
    except Exception:
        result = None
    with _lock:
        if result:
            _cache[key] = result
        else:
            _cache[key] = {"narrative": None, "source": "rules"}
        _pending.discard(key)


def get_narrative(key: tuple, facts_text: str, fallback: str) -> tuple[str, str]:
    if not llm.enabled():
        return fallback, "rules"
    with _lock:
        cached = _cache.get(key)
        if cached is None and key not in _pending:
            _pending.add(key)
            threading.Thread(target=_work, args=(key, facts_text), daemon=True).start()
    if cached and cached["narrative"]:
        return cached["narrative"], "llm"
    return fallback, "rules"


def clear() -> None:
    with _lock:
        _cache.clear()
