"""Deterministic, water-only spectral feature helpers."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np


def _ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """Return a safe normalized difference, preserving array shape."""
    with np.errstate(divide="ignore", invalid="ignore"):
        value = (numerator - denominator) / (numerator + denominator)
    return np.nan_to_num(value, nan=0.0, posinf=0.0, neginf=0.0)


def compute_spectral_features(bands: Mapping[str, Any]) -> dict[str, np.ndarray]:
    """Compute common Sentinel-2 water/bloom proxies from B03/B04/B05/B08.

    Inputs are arrays or array-like objects. No external service or calibration
    data is consulted; callers remain responsible for local calibration.
    """
    required = ("B03", "B04", "B05", "B08")
    missing = [name for name in required if name.upper() not in {k.upper() for k in bands}]
    if missing:
        raise ValueError(f"missing spectral bands: {', '.join(missing)}")
    normalized = {str(key).upper(): np.asarray(value, dtype=float) for key, value in bands.items()}
    shapes = {array.shape for array in normalized.values() if array.size}
    if len(shapes) > 1:
        raise ValueError("spectral bands must have matching shapes")
    b03, b04, b05, b08 = (normalized[name] for name in required)
    return {
        "ndwi": _ratio(b03, b08),
        "ndvi": _ratio(b08, b04),
        "ndci": _ratio(b05, b04),
        "fai_proxy": b05 - (b04 + (b08 - b04) * (740.0 - 665.0) / (842.0 - 665.0)),
    }


def summarize_spectral_features(features: Mapping[str, Any]) -> dict[str, float]:
    """Return finite means suitable for JSON/API responses."""
    summary: dict[str, float] = {}
    for name, values in features.items():
        array = np.asarray(values, dtype=float)
        summary[name] = float(np.nanmean(array)) if array.size else 0.0
    return summary


# Friendly aliases for callers that prefer shorter names.
spectral_features = compute_spectral_features
summarize = summarize_spectral_features
