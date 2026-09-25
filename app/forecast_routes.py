"""API routes exposing app.forecast's real WHO-baseline risk fusion.

This wires forecast_district_risk()/forecast_districts() — already real,
tested logic that blends the repository's annual WHO Malawi cholera
baseline (data/who_cholera_malawi.csv) with spectral and rainfall
signals — to HTTP, so the frontend can display it. No new forecasting
logic is added here; this only exposes what app/forecast.py already does.
"""
from __future__ import annotations

from typing import Any, Mapping

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.forecast import forecast_district_risk, forecast_districts

router = APIRouter(prefix="/forecast", tags=["forecast"])

# A small set of demo districts near the existing borehole/network data,
# with placeholder satellite components. Real per-district spectral
# scores would come from running /analyze per district in a fuller
# integration; until then these are clearly-labelled illustrative
# satellite inputs, while the cholera/WHO baseline blended in is real.
_DEMO_DISTRICTS: dict[str, dict[str, float]] = {
    "Salima": {"mndwi": 0.62, "turbidity": 0.58, "chlorophyll_a": 0.71, "ndci": 0.64},
    "Nkhotakota": {"mndwi": 0.41, "turbidity": 0.33, "chlorophyll_a": 0.29, "ndci": 0.35},
    "Dedza": {"mndwi": 0.18, "turbidity": 0.15, "chlorophyll_a": 0.12, "ndci": 0.10},
}


class DistrictForecastRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    district: str
    satellite: dict[str, float] | None = None
    rainfall: float | dict[str, float] | None = None
    cholera_rows: list[dict[str, Any]] = Field(default_factory=list)
    as_of: str | None = None


class AllDistrictsForecastRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    cholera_rows: list[dict[str, Any]] = Field(default_factory=list)
    as_of: str | None = None


@router.post("/district")
def forecast_one_district(request: DistrictForecastRequest) -> dict[str, Any]:
    satellite = request.satellite or _DEMO_DISTRICTS.get(request.district, {})
    return forecast_district_risk(
        request.district,
        satellite=satellite,
        rainfall=request.rainfall,
        cholera_rows=request.cholera_rows,
        as_of=request.as_of,
    )


@router.post("/all")
def forecast_all_districts(request: AllDistrictsForecastRequest) -> list[dict[str, Any]]:
    return forecast_districts(
        _DEMO_DISTRICTS,
        cholera_rows=request.cholera_rows,
        as_of=request.as_of,
    )


@router.get("/baseline")
def get_national_baseline() -> dict[str, Any]:
    """Return the raw WHO Malawi national annual baseline rows as-is,
    so the frontend can chart real history without recomputing anything.
    """
    from pathlib import Path
    import csv

    path = Path(__file__).resolve().parents[1] / "data" / "who_cholera_malawi.csv"
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            rows = [
                {"year": int(row["year"]), "reported_cases": int(row["reported_cases"])}
                for row in csv.DictReader(handle)
            ]
    except (OSError, ValueError):
        rows = []
    return {
        "source": "WHO Malawi national cholera surveillance (via HDX)",
        "coverage": f"{rows[0]['year']}\u2013{rows[-1]['year']}" if rows else "unavailable",
        "rows": rows,
    }
