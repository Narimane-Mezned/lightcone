import re

from . import llm
from .models import IntentOut, NeedSpec

SYSTEM = """You convert a cargo booking request written in plain language into constraints.
The resource is cargo space (kg) on the next Earth-Mars ship. Light delay makes negotiation impossible,
so the constraints must capture what the requester really needs.

Return ONLY a JSON object with these keys:
- "min_qty": number, the smallest amount in kg that is still useful to the requester
- "max_qty": number, the largest amount in kg that is useful
- "category": one of "medical", "science", "commercial"
- "can_defer": true if the requester says they can wait for the next ship or are flexible, otherwise false
- "summary": one short sentence (max 20 words) restating the need
- "notes": a list of short strings describing any assumption you made

Rules:
- Never invent quantities. Use only numbers present in the text.
- If only one quantity is given, use it for both min_qty and max_qty.
- If the text gives a minimum but no maximum, use the minimum for both.
- min_qty must be less than or equal to max_qty.
- If unsure about can_defer, use false.
"""

MEDICAL = re.compile(r"medic|clinic|patient|hospital|drug|vaccine|surg|treatment|health|oxygen", re.I)
SCIENCE = re.compile(r"scien|research|experiment|sample|instrument|lab\b|laboratory|study", re.I)
DEFER_YES = re.compile(r"can wait|next ship|next window|flexible|not urgent|no rush|can be delayed", re.I)
DEFER_NO = re.compile(r"cannot wait|can't wait|must|urgent|critical|immediately|life|before the", re.I)
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
    category = "medical" if MEDICAL.search(text) else "science" if SCIENCE.search(text) else "commercial"
    can_defer = bool(DEFER_YES.search(text)) and not bool(DEFER_NO.search(text))
    summary = f"Needs {min_qty:g}-{max_qty:g} kg ({category}), {'can' if can_defer else 'cannot'} wait for the next ship."
    return NeedSpec(min_qty=min_qty, max_qty=max_qty, category=category, can_defer=can_defer, summary=summary), notes


def _validate(raw: dict, text: str) -> tuple[NeedSpec, list[str]]:
    needs = NeedSpec(
        min_qty=float(raw["min_qty"]),
        max_qty=float(raw["max_qty"]),
        category=raw.get("category", "commercial"),
        can_defer=bool(raw.get("can_defer", False)),
        summary=str(raw.get("summary", ""))[:200],
    )
    allowed = _numbers(text)
    if needs.min_qty not in allowed or needs.max_qty not in allowed:
        raise ValueError("model produced a quantity that is not in the text")
    if needs.min_qty > needs.max_qty or needs.max_qty <= 0:
        raise ValueError("invalid range")
    notes = [str(n) for n in raw.get("notes", [])][:5]
    return needs, notes


def compile_intent(text: str) -> IntentOut:
    if llm.enabled():
        try:
            raw = llm.chat_json(SYSTEM, text)
            needs, notes = _validate(raw, text)
            return IntentOut(needs=needs, source="llm", model=llm.MODEL, notes=notes)
        except Exception as error:
            needs, notes = parse_rules(text)
            notes.insert(0, f"AI unavailable or rejected by guardrail ({type(error).__name__}); rule-based parser used.")
            return IntentOut(needs=needs, source="rules", model="rules", notes=notes)
    needs, notes = parse_rules(text)
    notes.insert(0, "AI disabled (no API key); rule-based parser used.")
    return IntentOut(needs=needs, source="rules", model="rules", notes=notes)
