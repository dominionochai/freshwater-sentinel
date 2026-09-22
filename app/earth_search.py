"""Public Earth Search STAC discovery and Sentinel-2 COG scene loading."""
from __future__ import annotations

from datetime import date
from typing import Any, Mapping, Sequence

import httpx
import numpy as np
import rasterio

from app.pipeline import REQUIRED_BANDS, Scene

EARTH_SEARCH_URL = "https://earth-search.aws.element84.com/v1"
DEFAULT_COLLECTION = "sentinel-2-l2a"
BAND_ASSET_KEYS: dict[str, tuple[str, ...]] = {
    "B02": ("B02", "blue"),
    "B03": ("B03", "green"),
    "B04": ("B04", "red"),
    "B05": ("B05", "rededge1", "rededge"),
    "B08": ("B08", "nir"),
    "B11": ("B11", "swir16", "swir-16"),
}


class EarthSearchError(RuntimeError):
    """Raised when a public STAC item or COG asset is unusable."""


def _json_response(response: httpx.Response) -> dict[str, Any]:
    try:
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise EarthSearchError(f"Earth Search request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise EarthSearchError("Earth Search returned a non-object JSON response")
    return payload


def search_earth_search(
    *,
    bbox: Sequence[float],
    datetime_range: str,
    cloud_cover: float | None = 20.0,
    limit: int = 10,
    endpoint: str = EARTH_SEARCH_URL,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    """Search the public Sentinel-2 L2A collection; never synthesize a scene."""
    if len(bbox) != 4:
        raise ValueError("bbox must contain west, south, east, north")
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")
    payload: dict[str, Any] = {
        "collections": [DEFAULT_COLLECTION],
        "bbox": [float(value) for value in bbox],
        "datetime": datetime_range,
        "limit": limit,
    }
    if cloud_cover is not None:
        payload["query"] = {"eo:cloud_cover": {"lte": float(cloud_cover)}}
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.post(f"{endpoint.rstrip('/')}/search", json=payload)
    except httpx.HTTPError as exc:
        raise EarthSearchError(f"Earth Search network request failed: {exc}") from exc
    result = _json_response(response)
    features = result.get("features")
    if not isinstance(features, list):
        raise EarthSearchError("Earth Search response did not contain a feature list")
    return [feature for feature in features if isinstance(feature, dict)]


def _asset_hrefs(item: Mapping[str, Any]) -> dict[str, str]:
    assets = item.get("assets")
    if not isinstance(assets, Mapping):
        raise EarthSearchError("STAC item has no assets object")
    hrefs: dict[str, str] = {}
    missing: list[str] = []
    for band, candidates in BAND_ASSET_KEYS.items():
        for candidate in candidates:
            asset = assets.get(candidate)
            if isinstance(asset, Mapping) and isinstance(asset.get("href"), str):
                hrefs[band] = asset["href"]
                break
        if band not in hrefs:
            missing.append(band)
    if missing:
        raise EarthSearchError("STAC item is missing required assets: " + ", ".join(missing))
    return hrefs


def _acquisition_date(item: Mapping[str, Any]) -> date:
    properties = item.get("properties")
    if not isinstance(properties, Mapping):
        raise EarthSearchError("STAC item has no properties object")
    raw = properties.get("datetime") or properties.get("dtr:start_datetime")
    if not isinstance(raw, str) or len(raw) < 10:
        raise EarthSearchError("STAC item has no verifiable acquisition datetime")
    try:
        return date.fromisoformat(raw[:10])
    except ValueError as exc:
        raise EarthSearchError(f"Invalid STAC acquisition datetime: {raw}") from exc


def _scene_metadata(item: Mapping[str, Any], hrefs: Mapping[str, str], endpoint: str) -> dict[str, Any]:
    properties = item.get("properties")
    if not isinstance(properties, Mapping):
        properties = {}
    metadata: dict[str, Any] = {
        "source_type": "earth_search_stac_cog",
        "stac_api": endpoint.rstrip("/"),
        "collection": item.get("collection"),
        "item_id": item.get("id"),
        "item_url": item.get("self") or item.get("id"),
        "assets": dict(hrefs),
        "cloud_cover": properties.get("eo:cloud_cover"),
        "platform": properties.get("platform"),
        "processing_baseline": properties.get("s2:processing_baseline"),
        "bbox": item.get("bbox"),
        "geometry": item.get("geometry"),
    }
    return {key: value for key, value in metadata.items() if value is not None}


def scene_from_stac_item(
    item: Mapping[str, Any], *, water_body_id: str, endpoint: str = EARTH_SEARCH_URL
) -> Scene:
    """Open all six required Sentinel-2 COGs referenced by one real item."""
    if item.get("type") not in (None, "Feature"):
        raise EarthSearchError("STAC payload is not a Feature item")
    item_id = item.get("id")
    if not isinstance(item_id, str) or not item_id:
        raise EarthSearchError("STAC item has no id")
    hrefs = _asset_hrefs(item)
    arrays: dict[str, np.ndarray] = {}
    try:
        for band in REQUIRED_BANDS:
            with rasterio.open(hrefs[band]) as dataset:
                arrays[band] = dataset.read(1).astype(np.float32, copy=False)
    except (rasterio.errors.RasterioError, OSError, ValueError) as exc:
        raise EarthSearchError(f"Unable to read COG assets for {item_id}: {exc}") from exc
    shapes = {array.shape for array in arrays.values()}
    if len(shapes) != 1:
        raise EarthSearchError(f"COG assets for {item_id} have inconsistent shapes: {shapes}")
    return Scene(
        water_body_id=water_body_id,
        acquisition_date=_acquisition_date(item),
        bands=arrays,
        source=f"earth-search:{item_id}",
        metadata=_scene_metadata(item, hrefs, endpoint),
    )


def scene_from_stac_item_url(
    item_url: str, *, water_body_id: str, endpoint: str = EARTH_SEARCH_URL, timeout: float = 30.0
) -> Scene:
    """Fetch one public STAC item URL and open its referenced COG assets."""
    if not item_url.startswith(("https://", "http://")):
        raise EarthSearchError("stac_item_url must be an http(s) URL")
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(item_url)
    except httpx.HTTPError as exc:
        raise EarthSearchError(f"STAC item network request failed: {exc}") from exc
    return scene_from_stac_item(_json_response(response), water_body_id=water_body_id, endpoint=endpoint)


def scene_from_earth_search(
    *, water_body_id: str, bbox: Sequence[float], datetime_range: str,
    cloud_cover: float | None = 20.0, endpoint: str = EARTH_SEARCH_URL, timeout: float = 30.0
) -> Scene:
    """Search Earth Search, select its first returned item, and load its COGs."""
    items = search_earth_search(
        bbox=bbox, datetime_range=datetime_range, cloud_cover=cloud_cover,
        endpoint=endpoint, timeout=timeout,
    )
    if not items:
        raise EarthSearchError("Earth Search returned no matching Sentinel-2 items")
    return scene_from_stac_item(items[0], water_body_id=water_body_id, endpoint=endpoint)
