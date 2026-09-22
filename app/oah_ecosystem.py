"""OneAquaHealth ecosystem dashboard adapter.

The public OneAquaHealth endpoint is intentionally treated as an optional
source. A failed request or an unexpected response degrades to an empty,
explicitly unsuccessful snapshot instead of taking down the application.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Literal, Iterator

import requests
from pydantic import BaseModel, ConfigDict, Field

OAH_ECOSYSTEM_URL = "https://api.enora-oah.eu/api/dashboards/city"
SOURCE = "oneaquahealth"
DEFAULT_TIMEOUT = 15.0


class OAHRecord(BaseModel):
    """A normalized dashboard/city record returned by OneAquaHealth."""

    model_config = ConfigDict(extra="allow")

    node_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OAHWaterNode(BaseModel):
    """WaterNode-compatible representation of an OAH record.

    The network builder can consume the common node keys, while nullable
    coordinates accurately represent that this endpoint does not publish
    coordinates for its European research sites.
    """

    model_config = ConfigDict(extra="allow")

    node_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    latitude: float | None = None
    longitude: float | None = None
    source: Literal["oneaquahealth"] = SOURCE
    source_url: str = OAH_ECOSYSTEM_URL
    fetched_at_utc: datetime
    city: str | None = None
    country: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def as_network_record(self) -> dict[str, Any]:
        """Return the common dictionary shape used by network ingestion."""

        return self.model_dump(mode="json")


# Useful names for callers that use the generic WaterNode terminology.
WaterNode = OAHWaterNode
WaterNodeCompatible = OAHWaterNode


class OAHFetchResult(BaseModel):
    """A fetch snapshot, including graceful-degradation status."""

    model_config = ConfigDict(extra="forbid")

    source: Literal["oneaquahealth"] = SOURCE
    source_url: str = OAH_ECOSYSTEM_URL
    fetched_at_utc: datetime
    ok: bool
    records: list[OAHRecord] = Field(default_factory=list)
    nodes: list[OAHWaterNode] = Field(default_factory=list)
    error: str | None = None

    def __iter__(self) -> Iterator[OAHRecord]:
        return iter(self.records)

    def __len__(self) -> int:
        return len(self.records)


def _first(values: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = values.get(key)
        if value not in (None, ""):
            return value
    return None


def _as_record_list(payload: Any) -> list[dict[str, Any]]:
    """Accept the common list and envelope shapes used by JSON APIs."""

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("records", "data", "cities", "dashboards", "results", "items"):
        candidate = payload.get(key)
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
        if isinstance(candidate, dict):
            nested = _as_record_list(candidate)
            if nested:
                return nested
    return [payload]


def _number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _utc(value: datetime | None = None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def normalize_records(payload: Any, *, fetched_at_utc: datetime | None = None) -> list[OAHRecord]:
    """Normalize an OAH response payload into validated Pydantic records."""

    normalized: list[OAHRecord] = []
    for index, raw in enumerate(_as_record_list(payload), start=1):
        attributes = raw.get("attributes")
        values = {**raw, **attributes} if isinstance(attributes, dict) else dict(raw)
        node_id = _first(values, "node_id", "waterpoint_id", "city_id", "dashboard_id", "code", "id")
        city = _first(values, "city", "municipality", "town")
        name = _first(values, "name", "label", "title", "site_name", "display_name", "city")
        node_id = str(node_id or f"oah-{index:04d}").strip()
        name = str(name or city or node_id).strip()
        excluded = {"node_id", "waterpoint_id", "city_id", "dashboard_id", "code", "id", "name", "label", "title", "site_name", "display_name", "city", "municipality", "town", "country", "latitude", "longitude", "lat", "lon", "lng", "attributes"}
        metadata = {key: value for key, value in raw.items() if key not in excluded}
        country = _first(values, "country", "country_name")
        record = OAHRecord(
            node_id=node_id,
            name=name,
            city=str(city) if city not in (None, "") else None,
            country=str(country) if country not in (None, "") else None,
            latitude=_number(_first(values, "latitude", "lat")),
            longitude=_number(_first(values, "longitude", "lon", "lng")),
            metadata=metadata,
        )
        normalized.append(record)
    return normalized


def to_water_nodes(records: Iterable[OAHRecord], *, fetched_at_utc: datetime) -> list[OAHWaterNode]:
    """Map normalized records to the repository's common water-node shape."""

    timestamp = _utc(fetched_at_utc)
    return [
        OAHWaterNode(
            node_id=record.node_id,
            name=record.name,
            latitude=record.latitude,
            longitude=record.longitude,
            source=SOURCE,
            source_url=OAH_ECOSYSTEM_URL,
            fetched_at_utc=timestamp,
            city=record.city,
            country=record.country,
            metadata=record.metadata,
        )
        for record in records
    ]


def fetch_oah_ecosystem(*, timeout: float = DEFAULT_TIMEOUT, endpoint: str = OAH_ECOSYSTEM_URL) -> OAHFetchResult:
    """Fetch the public OAH city dashboard and degrade safely on failure."""

    fetched_at = _utc()
    try:
        response = requests.get(endpoint, timeout=timeout)
        response.raise_for_status()
        records = normalize_records(response.json(), fetched_at_utc=fetched_at)
        return OAHFetchResult(
            source_url=endpoint,
            fetched_at_utc=fetched_at,
            ok=True,
            records=records,
            nodes=to_water_nodes(records, fetched_at_utc=fetched_at),
        )
    except (requests.RequestException, ValueError, TypeError) as exc:
        return OAHFetchResult(
            source_url=endpoint,
            fetched_at_utc=fetched_at,
            ok=False,
            error=f"{type(exc).__name__}: {exc}",
        )


fetch_ecosystem = fetch_oah_ecosystem
normalize_oah_records = normalize_records
