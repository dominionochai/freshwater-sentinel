"""Multispectral water detection with an optional OmniWaterMask adapter.

The original MNDWI/NDVI masking approach remains the default and is used
whenever the optional OmniWaterMask dependency is unavailable or fails.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from config import MNDWI_MIN, NDVI_MAX_FOR_WATER, REFLECTANCE_MAX, REFLECTANCE_MIN

REQUIRED_MASK_BANDS = ("B03", "B04", "B08", "B11")

try:  # Optional dependency: importing this module must never require it.
    import omniwatermask as _omniwatermask
except Exception:  # pragma: no cover - depends on the deployment environment
    _omniwatermask = None


def _index(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """Compute a normalized difference without divide-by-zero warnings."""
    total = numerator + denominator
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.divide(
            numerator - denominator,
            total,
            where=total != 0,
            out=np.full_like(numerator, np.nan, dtype=float),
        )


def _fallback_water_mask(
    bands: dict[str, np.ndarray],
) -> tuple[np.ndarray, dict[str, float]]:
    """Return the established MNDWI/NDVI mask and its diagnostics."""
    missing = [band for band in REQUIRED_MASK_BANDS if band not in bands]
    if missing:
        raise ValueError(f"missing required water-mask bands: {', '.join(missing)}")

    green, red, nir, swir1 = (
        np.asarray(bands[key], dtype=float) for key in REQUIRED_MASK_BANDS
    )
    if len({array.shape for array in (green, red, nir, swir1)}) != 1:
        raise ValueError("water-mask bands must have identical shapes")

    mndwi = _index(green, swir1)
    ndvi = _index(nir, red)
    finite = (
        np.isfinite(green)
        & np.isfinite(red)
        & np.isfinite(nir)
        & np.isfinite(swir1)
    )
    plausible = np.all(
        [
            (array >= REFLECTANCE_MIN) & (array <= REFLECTANCE_MAX)
            for array in (green, red, nir, swir1)
        ],
        axis=0,
    )
    mask = finite & plausible & (mndwi >= MNDWI_MIN) & (ndvi <= NDVI_MAX_FOR_WATER)
    diagnostics = {
        "mndwi_mean_candidate": float(np.nanmean(mndwi)) if np.isfinite(mndwi).any() else 0.0,
        "ndvi_mean_candidate": float(np.nanmean(ndvi)) if np.isfinite(ndvi).any() else 0.0,
        "water_fraction": float(mask.mean()),
        "water_mask_method": "mndwi_ndvi",
    }
    return mask, diagnostics


def _optional_omni_mask(bands: dict[str, np.ndarray]) -> np.ndarray | None:
    """Call common OmniWaterMask entry points, returning ``None`` on failure.

    OmniWaterMask has intentionally remained an optional integration point:
    deployments can install their preferred MIT implementation without making
    the base API or import path depend on it.
    """
    if _omniwatermask is None:
        return None
    try:
        predictor: Any = getattr(_omniwatermask, "predict", None)
        if predictor is None:
            predictor = getattr(_omniwatermask, "create_water_mask", None)
        if predictor is None:
            model_type = getattr(_omniwatermask, "OmniWaterMask", None)
            if model_type is not None:
                model = model_type()
                predictor = getattr(model, "predict", model)
        if predictor is None:
            return None
        result = predictor(bands)
        if isinstance(result, tuple):
            result = result[0]
        if isinstance(result, dict):
            result = result.get("mask")
        if result is None:
            return None
        mask = np.asarray(result, dtype=bool)
        expected_shape = np.asarray(next(iter(bands.values()))).shape
        if mask.shape != expected_shape:
            return None
        return mask
    except Exception:  # pragma: no cover - third-party implementation boundary
        return None


def create_water_mask(
    bands: dict[str, np.ndarray],
    use_omniwatermask: bool = False,
) -> tuple[np.ndarray, dict[str, float | str]]:
    """Return a boolean open-water mask and diagnostics.

    ``use_omniwatermask`` is deliberately default-off.  When enabled, a
    compatible OmniWaterMask installation is attempted first; the established
    MNDWI/NDVI implementation is the automatic fallback for missing,
    incompatible, or failing optional installations.
    """
    fallback_mask, diagnostics = _fallback_water_mask(bands)
    if use_omniwatermask:
        omni_mask = _optional_omni_mask(bands)
        if omni_mask is not None:
            return omni_mask, {
                **diagnostics,
                "water_fraction": float(omni_mask.mean()),
                "water_mask_method": "omniwatermask",
            }
    return fallback_mask, diagnostics
