"""Multispectral water detection with strict finite-value handling."""

from __future__ import annotations

import numpy as np

from config import MNDWI_MIN, NDVI_MAX_FOR_WATER, REFLECTANCE_MAX, REFLECTANCE_MIN

REQUIRED_MASK_BANDS = ("B03", "B04", "B08", "B11")


def _index(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    """Compute a normalized difference without divide-by-zero warnings."""
    total = numerator + denominator
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.divide(numerator - denominator, total, where=total != 0, out=np.full_like(numerator, np.nan, dtype=float))


def create_water_mask(bands: dict[str, np.ndarray]) -> tuple[np.ndarray, dict[str, float]]:
    """Return a boolean open-water mask; downstream analysis must use this mask."""
    missing = [band for band in REQUIRED_MASK_BANDS if band not in bands]
    if missing:
        raise ValueError(f"missing required water-mask bands: {', '.join(missing)}")
    green, red, nir, swir1 = (np.asarray(bands[key], dtype=float) for key in REQUIRED_MASK_BANDS)
    if len({array.shape for array in (green, red, nir, swir1)}) != 1:
        raise ValueError("water-mask bands must have identical shapes")

    mndwi = _index(green, swir1)
    ndvi = _index(nir, red)
    finite = np.isfinite(green) & np.isfinite(red) & np.isfinite(nir) & np.isfinite(swir1)
    plausible = np.all([(array >= REFLECTANCE_MIN) & (array <= REFLECTANCE_MAX) for array in (green, red, nir, swir1)], axis=0)
    mask = finite & plausible & (mndwi >= MNDWI_MIN) & (ndvi <= NDVI_MAX_FOR_WATER)
    diagnostics = {
        "mndwi_mean_candidate": float(np.nanmean(mndwi)) if np.isfinite(mndwi).any() else 0.0,
        "ndvi_mean_candidate": float(np.nanmean(ndvi)) if np.isfinite(ndvi).any() else 0.0,
        "water_fraction": float(mask.mean()),
    }
    return mask, diagnostics
