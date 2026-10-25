from datetime import date

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .engine import Engine
from .fairness import run_fairness
from .link import compute_link
from .intent import compile_intent
from .models import FairnessOut, IntentIn, IntentOut, LinkInfo, RequestIn, RequestOut, ScenarioIn, StateOut

app = FastAPI(title="Lightcone API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=422, detail="date must be YYYY-MM-DD")


def _check_range(day: date) -> None:
    if not (1900 <= day.year <= 2049):
        raise HTTPException(status_code=422, detail="date must be between 1900 and 2049 (DE421 range)")


DEFAULT_DATE = date(2040, 1, 1)
_default = ScenarioIn(date=DEFAULT_DATE.isoformat())
_link = compute_link(DEFAULT_DATE)
engine = Engine(_default, _link["one_way_s"], _link["conjunction"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/link", response_model=LinkInfo)
def link(day: date | None = Query(default=None, alias="date")):
    day = day or date.today()
    _check_range(day)
    return compute_link(day)


@app.post("/api/scenario", response_model=StateOut)
def scenario(body: ScenarioIn):
    day = _parse_date(body.date)
    _check_range(day)
    if body.compression <= 0:
        raise HTTPException(status_code=422, detail="compression must be positive")
    if body.resource.capacity <= 0:
        raise HTTPException(status_code=422, detail="capacity must be positive")
    info = compute_link(day)
    engine.configure(body, info["one_way_s"], info["conjunction"])
    return engine.snapshot()


@app.post("/api/intent", response_model=IntentOut)
def intent(body: IntentIn):
    if not body.text.strip():
        raise HTTPException(status_code=422, detail="text is required")
    return compile_intent(body.text[:1000])


@app.post("/api/request", response_model=RequestOut)
def request(body: RequestIn):
    if body.needs:
        if body.needs.max_qty <= 0 or body.needs.min_qty < 0 or body.needs.min_qty > body.needs.max_qty:
            raise HTTPException(status_code=422, detail="needs must satisfy 0 <= min_qty <= max_qty and max_qty > 0")
    elif body.qty <= 0:
        raise HTTPException(status_code=422, detail="qty must be positive")
    if not body.actor.strip():
        raise HTTPException(status_code=422, detail="actor is required")
    return engine.submit(body)


@app.get("/api/state", response_model=StateOut)
def state():
    return engine.snapshot()


@app.post("/api/reset", response_model=StateOut)
def reset():
    engine.reset()
    return engine.snapshot()


@app.get("/api/fairness", response_model=FairnessOut)
def fairness(
    day: date | None = Query(default=None, alias="date"),
    trials: int = Query(default=10000, ge=100, le=100000),
    window_s: float = Query(default=1800.0, gt=0),
):
    day = day or date.today()
    _check_range(day)
    info = compute_link(day)
    return run_fairness(info["one_way_s"], trials, window_s)
