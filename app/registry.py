"""Typed, offline registry loading for WPdx-style water point rows."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias


MeasurementValue: TypeAlias = float | str | None


@dataclass(frozen=True, slots=True)
class WaterPoint:
    """A water point with the location and measurements available in source data."""

    id: str
    lat: float | None
    lon: float | None
    status: str | None
    source_type: str | None
    measurements: dict[str, MeasurementValue] = field(default_factory=dict)


# These values are copied only from data/malawi_boreholes.csv at the initial commit.
# The ``demo-`` prefix makes the provenance explicit when no configured CSV is present.
DEMO_SEED_RECORDS: tuple[WaterPoint, ...] = (
    WaterPoint(
        id="demo-khaoleya-borehole-4",
        lat=-15.92187567,
        lon=35.31535983,
        status=None,
        source_type="Borehole or tubewell",
        measurements={"turbidity_ntu": 0.1},
    ),
    WaterPoint(
        id="demo-chapenda-village-borehole",
        lat=-15.9854106,
        lon=34.4785667,
        status=None,
        source_type="Borehole or tubewell",
        measurements={"turbidity_ntu": None},
    ),
)


_ID_ALIASES = {
    "id",
    "waterpoint_id",
    "water_point_id",
    "waterpoint_name",
    "water_point_name",
    "name",
}
_LAT_ALIASES = {"lat", "latitude", "gps_latitude"}
_LON_ALIASES = {"lon", "lng", "longitude", "gps_longitude"}
_STATUS_ALIASES = {"status", "status_id", "waterpoint_status", "functionality_status"}
_SOURCE_TYPE_ALIASES = {
    "source_type",
    "waterpoint_type",
    "water_point_type",
    "water_tech",
    "water_technology",
    "source",
}
_CORE_COLUMNS = _ID_ALIASES | _LAT_ALIASES | _LON_ALIASES | _STATUS_ALIASES | _SOURCE_TYPE_ALIASES


def _header(value: str) -> str:
    """Normalise WPdx and checked-in extract headers to stable snake case."""

    return "_".join("".join(character if character.isalnum() else "_" for character in value.strip().lower()).split("_"))


def _value(row: dict[str, str], aliases: set[str]) -> str | None:
    for key, value in row.items():
        if _header(key) in aliases and value.strip():
            return value.strip()
    return None


def _number(value: str | None) -> float | None:
    if value is None or value.strip().lower() in {"", "na", "n/a", "null", "none"}:
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"Expected a numeric coordinate, got {value!r}") from exc


def _measurement(value: str) -> MeasurementValue:
    cleaned = value.strip()
    if not cleaned or cleaned.lower() in {"na", "n/a", "null", "none"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return cleaned


def _parse_row(row: dict[str, str], row_number: int) -> WaterPoint:
    normalised = {_header(key): value for key, value in row.items()}
    point_id = _value(normalised, _ID_ALIASES) or f"row-{row_number}"
    measurements = {
        _header(key): _measurement(value)
        for key, value in normalised.items()
        if _header(key) not in _CORE_COLUMNS
    }
    return WaterPoint(
        id=point_id,
        lat=_number(_value(normalised, _LAT_ALIASES)),
        lon=_number(_value(normalised, _LON_ALIASES)),
        status=_value(normalised, _STATUS_ALIASES),
        source_type=_value(normalised, _SOURCE_TYPE_ALIASES),
        measurements=measurements,
    )


def _load_csv(path: Path) -> list[WaterPoint]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return []
        return [_parse_row(row, index) for index, row in enumerate(reader, start=2)]


def load_registry(csv_path: str | Path | None = None) -> list[WaterPoint]:
    """Load a configured local CSV, or return explicitly labelled offline demo seeds.

    ``csv_path`` takes precedence over ``WATER_POINT_REGISTRY_CSV``.  This loader
    performs no network access.  Missing coordinates remain ``None`` and missing
    measurement cells remain ``None`` rather than being fabricated.
    """

    configured = csv_path if csv_path is not None else os.getenv("WATER_POINT_REGISTRY_CSV")
    if configured:
        path = Path(configured).expanduser()
        if path.is_file():
            return _load_csv(path)
    return list(DEMO_SEED_RECORDS)


# Descriptive alias for callers that prefer the domain term over the registry name.
load_water_points = load_registry
