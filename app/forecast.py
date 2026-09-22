"""Deterministic, offline forecast fusion for district cholera risk.

The module deliberately accepts already-fetched observations. It never calls a
remote service, so OpenWashData/WHO-shaped rows can be injected in tests or by
a caller responsible for provenance and transport.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Iterable, Mapping


DEFAULT_WEIGHTS = {
    "mndwi": 0.15,
    "turbidity": 0.15,
    "chlorophyll_a": 0.15,
    "ndci": 0.15,
    "rainfall": 0.20,
    "cholera": 0.20,
}


@dataclass(frozen=True)
class ForecastConfig:
    """Thresholds and weights used by :func:`forecast_district_risk`."""

    sample_max_age_days: int = 14
    case_lookback_days: int = 28
    warning_threshold: float = 0.45
    alert_threshold: float = 0.70
    case_scale: float = 10.0
    weights: Mapping[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))

    def __post_init__(self) -> None:
        if self.sample_max_age_days < 0 or self.case_lookback_days < 0:
            raise ValueError("lookback and sample ages must be non-negative")
        if self.case_scale <= 0:
            raise ValueError("case_scale must be positive")
        weights = dict(self.weights)
        if set(weights) != set(DEFAULT_WEIGHTS):
            raise ValueError(
                "weights must contain mndwi, turbidity, chlorophyll_a, ndci, rainfall, and cholera"
            )
        if any(value < 0 for value in weights.values()) or abs(sum(weights.values()) - 1.0) > 1e-9:
            raise ValueError("forecast weights must be non-negative and sum to 1")


def _date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
            values = [_number(item, float("nan")) for item in value]
            values = [item for item in values if item == item]
            return sum(values) / len(values) if values else default
        return default


def _pick(values: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in values and values[name] is not None:
            return values[name]
    return default


def _bounded_positive(value: Any, scale: float) -> float:
    return max(0.0, min(1.0, _number(value) / scale))


def _normalise_satellite(satellite: Mapping[str, Any] | None) -> dict[str, float]:
    """Map common satellite/OpenData names onto four deterministic scores."""
    raw = dict(satellite or {})
    if isinstance(raw.get("features"), Mapping):
        merged = dict(raw["features"])
        merged.update({key: value for key, value in raw.items() if key != "features"})
        raw = merged

    mndwi = _pick(raw, "mndwi", "MNDWI", "ndwi", "NDWI")
    if mndwi is None and isinstance(raw.get("water_mask"), (bool, int, float)):
        mndwi = raw["water_mask"]
    # Existing spectral_features.py uses B03/B08 as its water index. Reuse
    # that convention as a fallback without changing its public output.
    if mndwi is None:
        green = _pick(raw, "B03", "b03", "green")
        nir_or_swir = _pick(raw, "B08", "b08", "nir", "swir")
        if green is not None and nir_or_swir is not None:
            denominator = _number(green) + _number(nir_or_swir)
            mndwi = (_number(green) - _number(nir_or_swir)) / denominator if denominator else 0.0
    mndwi_score = max(0.0, min(1.0, (_number(mndwi) + 1.0) / 2.0)) if mndwi is not None else 0.0

    turbidity = _pick(raw, "turbidity", "turbidity_index", "turbidity_proxy", "ntu")
    if turbidity is None:
        red = _pick(raw, "B04", "b04", "red")
        green = _pick(raw, "B03", "b03", "green")
        turbidity = _number(red) / _number(green) if green is not None and _number(green) else 0.0
    # Accept either a [0, 1] proxy or a physical-ish NTU value.
    turbidity_score = _number(turbidity)
    turbidity_score = turbidity_score if 0.0 <= turbidity_score <= 1.0 else turbidity_score / 100.0
    turbidity_score = max(0.0, min(1.0, turbidity_score))

    chlorophyll = _pick(raw, "chlorophyll_a", "chlorophyll-a", "chl_a", "chlorophyll", "chlorophyll_proxy")
    chlorophyll_score = _number(chlorophyll)
    chlorophyll_score = chlorophyll_score if 0.0 <= chlorophyll_score <= 1.0 else chlorophyll_score / 100.0
    chlorophyll_score = max(0.0, min(1.0, chlorophyll_score))

    ndci = _pick(raw, "ndci", "NDCI")
    ndci_score = max(0.0, min(1.0, (_number(ndci) + 1.0) / 2.0)) if ndci is not None else 0.0
    return {"mndwi": mndwi_score, "turbidity": turbidity_score, "chlorophyll_a": chlorophyll_score, "ndci": ndci_score}


def _rainfall_score(rainfall: Any) -> float:
    if rainfall is None:
        return 0.0
    if isinstance(rainfall, Mapping):
        pressure = _pick(rainfall, "rainfall_pressure", "pressure")
        if pressure is not None:
            return max(0.0, min(1.0, _number(pressure)))
        recent = _pick(rainfall, "recent_3_total_mm", "recent_total_mm", "total_mm")
        return _bounded_positive(recent, 60.0)
    return _bounded_positive(rainfall, 60.0)


def _row_district(row: Mapping[str, Any]) -> str | None:
    value = _pick(row, "district", "district_name", "admin2", "admin_2", "location")
    return str(value) if value is not None else None


def _row_cases(row: Mapping[str, Any]) -> float:
    value = _pick(row, "cases", "cholera_cases", "confirmed_cases", "suspected_cases", "value", default=0)
    cases = max(0.0, _number(value))
    if cases == 0 and _pick(row, "lab_confirmed", "confirmed", default=False):
        cases = 1.0
    return cases


def _row_sample_date(row: Mapping[str, Any]) -> date | None:
    value = _pick(row, "lab_sample_date", "sample_date", "laboratory_date", "lab_date")
    if value is None and _pick(row, "lab_sample", "sample_collected", default=False):
        value = _pick(row, "date", "reported_date", "event_date")
    return _date(value)


def _resolve_as_of(rows: Iterable[Mapping[str, Any]], supplied: Any) -> date:
    resolved = _date(supplied)
    if resolved is not None:
        return resolved
    dates = [_date(_pick(row, "date", "reported_date", "event_date")) for row in rows]
    dates = [value for value in dates if value is not None]
    return max(dates) if dates else date.today()


def forecast_district_risk(
    district: str,
    satellite: Mapping[str, Any] | None = None,
    rainfall: Mapping[str, Any] | Iterable[float] | float | None = None,
    cholera_rows: Iterable[Mapping[str, Any]] = (),
    *,
    as_of: date | datetime | str | None = None,
    config: ForecastConfig | None = None,
    weights: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Fuse environmental and injectable health evidence into one district risk."""
    rows = [dict(row) for row in cholera_rows]
    effective_config = config or ForecastConfig()
    if weights is not None:
        effective_config = ForecastConfig(
            sample_max_age_days=effective_config.sample_max_age_days,
            case_lookback_days=effective_config.case_lookback_days,
            warning_threshold=effective_config.warning_threshold,
            alert_threshold=effective_config.alert_threshold,
            case_scale=effective_config.case_scale,
            weights=weights,
        )
    observed_on = _resolve_as_of(rows, as_of)
    start = observed_on - timedelta(days=effective_config.case_lookback_days)
    district_rows = [
        row
        for row in rows
        if (_row_district(row) is None or _row_district(row) == str(district))
        and (row_date := _row_sample_date(row)) is not None
        and start <= row_date <= observed_on
    ]
    cases = sum(_row_cases(row) for row in district_rows)
    case_score = max(0.0, min(1.0, cases / effective_config.case_scale))
    sample_dates = [sample for row in district_rows if (sample := _row_sample_date(row)) is not None and sample <= observed_on]
    latest_sample = max(sample_dates) if sample_dates else None
    sample_age = (observed_on - latest_sample).days if latest_sample else None
    field_sample_required = latest_sample is None or sample_age > effective_config.sample_max_age_days

    components = _normalise_satellite(satellite)
    components["rainfall"] = _rainfall_score(rainfall)
    components["cholera"] = case_score
    final_weights = dict(effective_config.weights)
    risk_score = sum(final_weights[name] * components[name] for name in final_weights)
    has_cases = cases > 0
    pre_case_warning = not has_cases and risk_score >= effective_config.warning_threshold
    if risk_score >= effective_config.alert_threshold:
        alert = "ALERT"
        risk_level = "high"
    elif pre_case_warning:
        alert = "PRE-CASE WARNING"
        risk_level = "moderate"
    elif risk_score >= effective_config.warning_threshold:
        alert = "WATCH"
        risk_level = "moderate"
    else:
        alert = "MONITOR"
        risk_level = "low"
    return {
        "district": str(district),
        "as_of": observed_on.isoformat(),
        "risk_score": round(risk_score, 6),
        "risk_level": risk_level,
        "alert": alert,
        "pre_case_warning": pre_case_warning,
        "components": {name: round(value, 6) for name, value in components.items()},
        "weights": final_weights,
        "cholera_cases": cases,
        "lab_sample_date": latest_sample.isoformat() if latest_sample else None,
        "sample_age_days": sample_age,
        "sample_max_age_days": effective_config.sample_max_age_days,
        "field_sample_required": field_sample_required,
        "action": "FIELD SAMPLE REQUIRED" if field_sample_required else alert,
        "data_source": "injected OpenWashData/WHO-style cholera rows",
    }


def forecast_districts(
    satellite_by_district: Mapping[str, Mapping[str, Any]],
    rainfall_by_district: Mapping[str, Any] | None = None,
    cholera_rows: Iterable[Mapping[str, Any]] = (),
    **kwargs: Any,
) -> list[dict[str, Any]]:
    """Forecast every district represented by the supplied satellite mapping."""
    rainfall_by_district = rainfall_by_district or {}
    rows = list(cholera_rows)
    return [
        forecast_district_risk(
            district,
            satellite=satellite,
            rainfall=rainfall_by_district.get(district),
            cholera_rows=rows,
            **kwargs,
        )
        for district, satellite in satellite_by_district.items()
    ]


def backtest_forecast(
    forecasts: Iterable[Mapping[str, Any]],
    cholera_rows: Iterable[Mapping[str, Any]],
    *,
    horizon_days: int = 42,
    case_threshold: float = 1.0,
) -> list[dict[str, Any]]:
    """Grade alerts against dated cases, returning HIT/MISS and actual lead time.

    A hit requires a dated positive case in the same district after the alert
    date and within ``horizon_days``. No correlation or row-order assumption is
    used; both dates are parsed and compared explicitly.
    """
    rows = [dict(row) for row in cholera_rows]
    outcomes: list[dict[str, Any]] = []
    for forecast in forecasts:
        district = str(_pick(forecast, "district", "district_name", "location", default=""))
        forecast_date = _date(_pick(forecast, "as_of", "forecast_date", "alert_date", "date"))
        base = {"district": district, "forecast_date": forecast_date.isoformat() if forecast_date else None}
        if forecast_date is None:
            outcomes.append({**base, "outcome": "MISS", "grade": "MISS", "lead_time_weeks": None, "reason": "missing forecast date"})
            continue
        events = []
        for row in rows:
            if _row_district(row) not in (None, district):
                continue
            event_date = _date(_pick(row, "date", "reported_date", "event_date"))
            if event_date is None or event_date < forecast_date or event_date > forecast_date + timedelta(days=horizon_days):
                continue
            if _row_cases(row) >= case_threshold:
                events.append(event_date)
        event_date = min(events) if events else None
        hit = event_date is not None
        lead = round((event_date - forecast_date).days / 7.0, 6) if event_date else None
        outcomes.append({**base, "outcome": "HIT" if hit else "MISS", "grade": "HIT" if hit else "MISS", "event_date": event_date.isoformat() if event_date else None, "lead_time_weeks": lead})
    return outcomes


# Friendly aliases for callers that use the shorter names.
forecast_risk = forecast_district_risk
backtest = backtest_forecast
