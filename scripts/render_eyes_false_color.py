"""Fetch one real Sentinel-2 L2A scene over the Lake Malawi basin and render
THREE PNGs for the EYES screen's band toggle: true color, false color
(NIR-red-green), and raw NIR grayscale.

This performs ONE real network fetch (bands B02/B03/B04/B08 all come from
the same scene) and renders three views from it locally, so switching
views in the UI never triggers another network call.

Run it once, locally, wherever you have real internet access.

Usage:
    python scripts/render_eyes_false_color.py

Output (all in data/):
    eyes_true_color_demo.png      B04/B03/B02 -> R/G/B (what the eye sees)
    eyes_false_color_demo.png     B08/B04/B03 -> R/G/B (bloom/veg signal)
    eyes_nir_demo.png             B08 alone, grayscale (raw infrared)
    eyes_false_color_demo.json    real scene metadata + honesty caption
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.earth_search import (  # noqa: E402
    EarthSearchError,
    search_earth_search,
    scene_from_stac_item,
)

# Lake Malawi basin, southern portion near the Salima/Nkhotakota borehole
# cluster used elsewhere in the demo data.
BBOX = [34.0, -14.2, 35.4, -13.4]
DATETIME_RANGE = "2025-01-01T00:00:00Z/2026-09-23T23:59:59Z"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_TRUE_COLOR = OUTPUT_DIR / "eyes_true_color_demo.png"
OUTPUT_FALSE_COLOR = OUTPUT_DIR / "eyes_false_color_demo.png"
OUTPUT_NIR = OUTPUT_DIR / "eyes_nir_demo.png"
OUTPUT_META = OUTPUT_DIR / "eyes_false_color_demo.json"


def _stretch(band: np.ndarray, low_pct: float = 2.0, high_pct: float = 98.0) -> np.ndarray:
    """Contrast-stretch one band to 0-255 using percentile clipping.

    Satellite reflectance values are not naturally in a display-friendly
    range; a straight linear map from raw values would look almost black.
    A percentile stretch is standard practice for both true-color and
    false-color rendering.
    """
    finite = band[np.isfinite(band)]
    if finite.size == 0:
        return np.zeros_like(band, dtype=np.uint8)
    lo, hi = np.percentile(finite, [low_pct, high_pct])
    if hi <= lo:
        hi = lo + 1e-6
    clipped = np.clip(band, lo, hi)
    scaled = (clipped - lo) / (hi - lo) * 255.0
    return np.nan_to_num(scaled, nan=0.0).astype(np.uint8)


def main() -> None:
    print(f"Searching Earth Search for Sentinel-2 L2A scenes over bbox {BBOX} ...")
    try:
        items = search_earth_search(
            bbox=BBOX, datetime_range=DATETIME_RANGE, cloud_cover=15.0, limit=10
        )
    except EarthSearchError as exc:
        print(f"Earth Search request failed: {exc}")
        print("Check your internet connection and try again.")
        sys.exit(1)

    if not items:
        print("No scenes found for this bbox/date range/cloud-cover filter.")
        print("Try widening DATETIME_RANGE or raising the cloud_cover limit.")
        sys.exit(1)

    item = items[0]
    props = item.get("properties", {})
    print(f"Using scene: {item.get('id')} | date {props.get('datetime')} "
          f"| cloud cover {props.get('eo:cloud_cover')}%")

    print("Downloading real Sentinel-2 COG band assets (B02, B03, B04, B08) ...")
    scene = scene_from_stac_item(item, water_body_id="demo-lake")

    blue = scene.bands["B02"].astype(float)
    green = scene.bands["B03"].astype(float)
    red = scene.bands["B04"].astype(float)
    nir = scene.bands["B08"].astype(float)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- True color: what the human eye would actually see ---
    true_rgb = np.dstack([_stretch(red), _stretch(green), _stretch(blue)])
    Image.fromarray(true_rgb, mode="RGB").save(OUTPUT_TRUE_COLOR)
    print(f"Saved true-color composite to {OUTPUT_TRUE_COLOR}")

    # --- False color: classic color-infrared rendering (NIR->R, R->G, G->B) ---
    false_rgb = np.dstack([_stretch(nir), _stretch(red), _stretch(green)])
    Image.fromarray(false_rgb, mode="RGB").save(OUTPUT_FALSE_COLOR)
    print(f"Saved false-color composite to {OUTPUT_FALSE_COLOR}")

    # --- Raw NIR: the actual infrared band alone, grayscale ---
    nir_gray = _stretch(nir)
    Image.fromarray(nir_gray, mode="L").save(OUTPUT_NIR)
    print(f"Saved raw NIR grayscale to {OUTPUT_NIR}")

    metadata = {
        "source": "earth_search_stac_cog",
        "item_id": item.get("id"),
        "acquisition_datetime": props.get("datetime"),
        "cloud_cover_pct": props.get("eo:cloud_cover"),
        "platform": props.get("platform"),
        "bbox": BBOX,
        "views": {
            "true_color": {
                "file": "eyes_true_color_demo.png",
                "bands": "B04->R, B03->G, B02->B",
                "label": "True color — what the human eye would see",
            },
            "false_color": {
                "file": "eyes_false_color_demo.png",
                "bands": "B08->R, B04->G, B03->B",
                "label": "False color (NIR) — vegetation and bloom signal, invisible to the eye",
            },
            "nir": {
                "file": "eyes_nir_demo.png",
                "bands": "B08 (842nm) grayscale",
                "label": "Raw near-infrared, 842nm — a single band the eye cannot perceive at all",
            },
        },
        "caption": (
            f"Sentinel-2 L2A, captured {str(props.get('datetime'))[:10]} "
            "— cached real scene, not a live tile fetch"
        ),
    }
    OUTPUT_META.write_text(json.dumps(metadata, indent=2))
    print(f"Saved scene metadata to {OUTPUT_META}")
    print("\nDone. Three views ready for the EYES band toggle:")
    print("  true color / false color / raw NIR")


if __name__ == "__main__":
    main()



if __name__ == "__main__":
    main()
