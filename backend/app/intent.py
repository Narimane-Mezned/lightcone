import re

from . import llm
from .models import IntentOut, NeedSpec

SYSTEM = """You convert a cargo booking request written in plain language into constraints.
The resource is cargo space (kg) on the next Earth-Mars ship. Light delay makes negotiation impossible,
so the constraints must capture what the requester really needs.

Return ONLY a JSON object with these keys:
- "min_qty": number, the smallest amount in kg that is still useful to the requester
- "max_qty": number, the largest amount in kg that is useful
- "category": one of "medical", "science", "commercial" (the requester's own purpose, not what they would yield for)
- "can_defer": true if the requester says they can wait for the next ship or are flexible, otherwise false
- "next_ship_value": number between 0 and 1: how much a kg delivered on the next ship is worth to them compared with a kg now
  (0 if they cannot wait at all, about 0.5 if waiting hurts but is acceptable, about 0.7 if they say they can wait, about 0.9 if they say it makes little difference)
- "yield_to_medical": true if they say they would give up some cargo for a medical emergency or for patients, otherwise false
- "yield_max_qty": number of kg they would give up for a medical need (0 if not stated)
- "summary": one short sentence (max 20 words) restating the need
- "notes": a list of short strings describing any assumption you made

Rules:
- Never invent quantities. Use only numbers present in the text.
- If only one quantity is given, use it for both min_qty and max_qty.
- If the text gives a minimum but no maximum, use the minimum for both.
- min_qty must be less than or equal to max_qty.
- If unsure about can_defer, use false. If can_defer is false, next_ship_value must be 0.
- yield_max_qty must be a number present in the text, or 0.
"""

MEDICAL = re.compile(r"medic|clinic|patient|hospital|drug|vaccine|surg|treatment|health|oxygen", re.I)
SCIENCE = re.compile(r"scien|research|experiment|sample|instrument|lab\b|laboratory|study", re.I)
DEFER_YES = re.compile(r"can wait|next ship|next window|flexible|not urgent|no rush|can be delayed", re.I)
DEFER_NO = re.compile(r"cannot wait|can't wait|must|urgent|critical|immediately|life|before the", re.I)
YIELD = re.compile(r"(?:give up|yield|release|spare)\s*(?:up to\s*)?(\d+(?:\.\d+)?)\s*(?:kg)?", re.I)
YIELD_CLAUSE = re.compile(r"[^.]*(?:give up|yield|release|spare)[^.]*", re.I)
YIELD_MEDICAL = re.compile(r"medical emergenc|patients? (?:need|first)|for a clinic|for medical", re.I)
LITTLE_DIFFERENCE = re.compile(r"no rush|makes little difference|doesn't matter|does not matter", re.I)
AT_LEAST = re.compile(r"(?:at least|minimum(?: of)?|min\.?|no less than)\s*(\d+(?:\.\d+)?)\s*(?:kg)?", re.I)
AT_MOST = re.compile(r"(?:up to|at most|maximum(?: of)?|max\.?|no more than|above)\s*(\d+(?:\.\d+)?)\s*(?:kg)?", re.I)
ANY_KG = re.compile(r"(\d+(?:\.\d+)?)\s*kg", re.I)


def _numbers(text: str) -> set[float]:
    return {float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)}


def parse_rules(text: str) -> tuple[NeedSpec, list[str]]:
    notes = []
    low = AT_LEAST.search(text)
    high = AT_MOST.search(text)
    amounts = [float(n) for n in ANY_KG.findall(text)]
    min_qty = float(low.group(1)) if low else None
    max_qty = float(high.group(1)) if high else None
    if min_qty is None and max_qty is None and amounts:
        min_qty = max_qty = amounts[0]
    if min_qty is None:
        min_qty = max_qty
    if max_qty is None:
        max_qty = min_qty
    if min_qty is None:
        min_qty = max_qty = 0.0
        notes.append("No quantity found in the text.")
    if min_qty > max_qty:
        min_qty, max_qty = max_qty, min_qty
    own_need = YIELD_CLAUSE.sub(" ", text)
    category = "medical" if MEDICAL.search(own_need) else "science" if SCIENCE.search(own_need) else "commercial"
    can_defer = bool(DEFER_YES.search(text)) and not bool(DEFER_NO.search(text))
    next_ship_value = (0.9 if LITTLE_DIFFERENCE.search(text) else 0.7) if can_defer else 0.0
    give = YIELD.search(text)
    yield_to_medical = bool(give) and bool(YIELD_MEDICAL.search(text))
    yield_max_qty = float(give.group(1)) if yield_to_medical else 0.0
    summary = f"Needs {min_qty:g}-{max_qty:g} kg ({category}), {'can' if can_defer else 'cannot'} wait for the next ship."
    if yield_to_medical:
        summary += f" Would give up {yield_max_qty:g} kg for a medical need."
    return NeedSpec(
        min_qty=min_qty,
        max_qty=max_qty,
        category=category,
        can_defer=can_defer,
        next_ship_value=next_ship_value,
        yield_to_medical=yield_to_medical,
        yield_max_qty=yield_max_qty,
        summary=summary,
    ), notes


def _validate(raw: dict, text: str) -> tuple[NeedSpec, list[str]]:
    needs = NeedSpec(
        min_qty=float(raw["min_qty"]),
        max_qty=float(raw["max_qty"]),
        category=raw.get("category", "commercial"),
        can_defer=bool(raw.get("can_defer", False)),
        next_ship_value=min(max(float(raw.get("next_ship_value", 0.0)), 0.0), 1.0),
        yield_to_medical=bool(raw.get("yield_to_medical", False)),
        yield_max_qty=float(raw.get("yield_max_qty", 0.0) or 0.0),
        summary=str(raw.get("summary", ""))[:200],
    )
    if not needs.can_defer:
        needs.next_ship_value = 0.0
    if not needs.yield_to_medical:
        needs.yield_max_qty = 0.0
    allowed = _numbers(text)
    if needs.min_qty not in allowed or needs.max_qty not in allowed:
        raise ValueError("model produced a quantity that is not in the text")
    if needs.yield_max_qty and needs.yield_max_qty not in allowed:
        raise ValueError("model produced a yield quantity that is not in the text")
    if needs.yield_max_qty > needs.min_qty:
        needs.yield_max_qty = needs.min_qty
    if needs.min_qty > needs.max_qty or needs.max_qty <= 0:
        raise ValueError("invalid range")
    notes = [str(n) for n in raw.get("notes", [])][:5]
    return needs, notes


def _reason(error: Exception) -> str:
    response = getattr(error, "response", None)
    code = getattr(response, "status_code", None)
    if code == 401:
        return "AI rejected the API key (401): check OPENROUTER_API_KEY in backend/.env."
    if code == 402:
        return "AI refused (402): the model is not free or the account needs credits; use a ':free' model."
    if code == 404:
        return "AI model not available (404): enable free model endpoints in OpenRouter privacy settings, or change LLM_MODELS."
    if code == 429:
        return "AI rate limit reached (429): wait a minute; free tier is about 20 requests/minute and 50/day."
    if code:
        return f"AI service error ({code})."
    if isinstance(error, ValueError):
        return f"AI answer rejected by guardrail ({error})."
    return f"AI unreachable ({type(error).__name__})."


def compile_intent(text: str) -> IntentOut:
    if llm.enabled():
        try:
            raw, model = llm.chat_json(SYSTEM, text)
            needs, notes = _validate(raw, text)
            return IntentOut(needs=needs, source="llm", model=model, notes=notes)
        except Exception as error:
            needs, notes = parse_rules(text)
            notes.insert(0, f"{_reason(error)} Rule-based parser used.")
            return IntentOut(needs=needs, source="rules", model="rules", notes=notes)
    needs, notes = parse_rules(text)
    notes.insert(0, "AI disabled (no API key); rule-based parser used.")
    return IntentOut(needs=needs, source="rules", model="rules", notes=notes)
