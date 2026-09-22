"""Sentinel-2 L2A preview and spectral-index helpers.

The downloader deliberately makes no pixel claims when the preview or JP2 assets
are unavailable. It tries the public Sentinel COG S3 URL first, then the Azure
mirror, and walks backwards by date after a 404. NDWI/NDVI are only computed
from bytes successfully downloaded and decoded by rasterio; metadata/preview
availability alone never produces fabricated pixel statistics.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Any, Callable

import numpy as np
import requests

try:
    import rasterio
except ImportError:  # pragma: no cover
    rasterio = None  # type: ignore[assignment]

S3_ROOT = "https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs"
AZURE_ROOT = "https://ai4edataeuwest.blob.core.windows.net/sentinel-2-l2a-cogs"
WATER_NDWI_THRESHOLD = 0.0
DEFAULT_LOOKBACK_DAYS = 30


def _as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def _tile_path(tile: str) -> str:
    parts = tile.strip().upper().replace("_", "/").split("/")
    if len(parts) == 1 and len(parts[0]) == 5:
        parts = [parts[0][:2], parts[0][2], parts[0][3:]]
    if len(parts) != 3:
        raise ValueError("tile must look like '36/L/VM' or '36LVM'")
    return "/".join(parts)


def _asset_url(root: str, tile: str, scene_date: date, asset: str, item_id: str | None) -> str:
    item_or_date = item_id or scene_date.strftime("%Y%m%d")
    return f"{root}/{_tile_path(tile)}/{scene_date.year}/{scene_date.month}/{item_or_date}/{asset}"


def preview_urls(tile: str, scene_date: str | date | datetime, item_id: str | None = None) -> tuple[str, str]:
    day = _as_date(scene_date)
    return (_asset_url(S3_ROOT, tile, day, "preview.jpg", item_id), _asset_url(AZURE_ROOT, tile, day, "preview.jpg", item_id))


def band_urls(tile: str, scene_date: str | date | datetime, band: str, item_id: str | None = None) -> tuple[str, str]:
    if band not in {"B03", "B04", "B08"}:
        raise ValueError("only B03, B04, and B08 are supported")
    day = _as_date(scene_date)
    return (_asset_url(S3_ROOT, tile, day, f"{band}.jp2", item_id), _asset_url(AZURE_ROOT, tile, day, f"{band}.jp2", item_id))


def _download(url: str, timeout: float = 30.0) -> bytes:
    response = requests.get(url, timeout=timeout)
    if response.status_code == 404:
        raise FileNotFoundError(url)
    response.raise_for_status()
    return response.content


def _first_available(urls: tuple[str, ...], downloader: Callable[[str], bytes]) -> tuple[bytes, str]:
    for url in urls:
        try:
            return downloader(url), url
        except (FileNotFoundError, requests.HTTPError):
            continue
    raise FileNotFoundError("asset unavailable from all mirrors")


def fetch_preview(tile: str, scene_date: str | date | datetime, *, item_id: str | None = None, max_lookback_days: int = DEFAULT_LOOKBACK_DAYS, downloader: Callable[[str], bytes] = _download) -> dict[str, Any]:
    """Fetch preview S3-first, then Azure, walking backwards after misses."""
    requested = _as_date(scene_date)
    for offset in range(max_lookback_days + 1):
        candidate = requested - timedelta(days=offset)
        try:
            payload, url = _first_available(
                preview_urls(tile, candidate, item_id if candidate == requested else None), downloader
            )
            return {"scene_date": candidate.isoformat(), "url": url, "content": payload}
        except FileNotFoundError:
            continue
    return {"scene_date": requested.isoformat(), "url": None, "content": None}


def _read_band(payload: bytes) -> np.ndarray:
    if rasterio is None:
        raise RuntimeError("rasterio is required to decode Sentinel JP2 band bytes")
    with rasterio.open(BytesIO(payload)) as dataset:
        return dataset.read(1).astype(np.float64)


def _safe_ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.divide(numerator, denominator, out=np.full_like(numerator, np.nan, dtype=float), where=denominator != 0)


def compute_indices(green: np.ndarray, nir: np.ndarray, red: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | None]:
    """Compute NDWI and, when red is supplied, NDVI without changing pixels."""
    green_array, nir_array = np.asarray(green, dtype=float), np.asarray(nir, dtype=float)
    if green_array.shape != nir_array.shape:
        raise ValueError("green and NIR arrays must have the same shape")
    ndwi = _safe_ratio(green_array - nir_array, green_array + nir_array)
    ndvi = None
    if red is not None:
        red_array = np.asarray(red, dtype=float)
        if red_array.shape != nir_array.shape:
            raise ValueError("red and NIR arrays must have the same shape")
        ndvi = _safe_ratio(nir_array - red_array, nir_array + red_array)
    return ndwi, ndvi


def summarize_ndwi(ndwi: np.ndarray, *, threshold: float = WATER_NDWI_THRESHOLD) -> dict[str, Any]:
    """Summarize finite NDWI values and classify water with a boolean mask."""
    values = np.asarray(ndwi, dtype=float)
    finite = np.isfinite(values)
    if not finite.any():
        return {"ndwi_min": None, "ndwi_mean": None, "ndwi_max": None, "water_pixel_share": None, "anomaly_flag": False}
    valid = values[finite]
    water_share = float((values > threshold)[finite].mean())
    return {"ndwi_min": float(valid.min()), "ndwi_mean": float(valid.mean()), "ndwi_max": float(valid.max()), "water_pixel_share": water_share, "anomaly_flag": bool(water_share > 0.5)}


def analyze_scene(tile: str, scene_date: str | date | datetime, *, item_id: str | None = None, max_lookback_days: int = DEFAULT_LOOKBACK_DAYS, downloader: Callable[[str], bytes] = _download) -> dict[str, Any]:
    """Return stats, or explicit null stats when JP2 pixels cannot be decoded."""
    preview = fetch_preview(tile, scene_date, item_id=item_id, max_lookback_days=max_lookback_days, downloader=downloader)
    effective_date = preview["scene_date"]
    payloads: dict[str, bytes] = {}
    for band in ("B03", "B08", "B04"):
        try:
            payloads[band], _ = _first_available(band_urls(tile, effective_date, band, item_id), downloader)
        except (FileNotFoundError, RuntimeError, ValueError):
            continue
    result: dict[str, Any] = {"scene_date": effective_date, "ndwi_min": None, "ndwi_mean": None, "ndwi_max": None, "water_pixel_share": None, "anomaly_flag": False}
    if {"B03", "B08"}.issubset(payloads):
        try:
            green, nir = _read_band(payloads["B03"]), _read_band(payloads["B08"])
            red = _read_band(payloads["B04"]) if "B04" in payloads else None
            ndwi, _ndvi = compute_indices(green, nir, red)
            result.update(summarize_ndwi(ndwi))
        except (RuntimeError, ValueError, OSError):
            pass
    return result


fetch_sentinel_preview = fetch_preview
analyze_sentinel_scene = analyze_scene
__all__ = ["analyze_scene", "analyze_sentinel_scene", "band_urls", "compute_indices", "fetch_preview", "fetch_sentinel_preview", "preview_urls", "summarize_ndwi"]
