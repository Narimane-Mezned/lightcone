from datetime import date

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .link import compute_link
from .models import LinkInfo

app = FastAPI(title="Lightcone API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/link", response_model=LinkInfo)
def link(day: date | None = Query(default=None, alias="date")):
    return compute_link(day or date.today())
