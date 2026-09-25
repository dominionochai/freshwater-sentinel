"""Render EYES-screen PNGs from a locally generated sample scene (no network)."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.make_sample_scene import create_sample_scene, BANDS  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_TRUE_COLOR = OUTPUT_DIR / "eyes_true_color_demo.png"
OUTPUT_FALSE_COLOR = OUTPUT_DIR / "eyes_false_color_demo.png"
OUTPUT_NIR = OUTPUT_DIR / "eyes_nir_demo.png"
OUTPUT_META = OUTPUT_DIR / "eyes_false_color_demo.json"


def _stretch(band: np.ndarray, low_pct: float = 2.0, high_pct: float = 98.0) -> np.ndarray:
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
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scene_path = create_sample_scene(OUTPUT_DIR / "sample_scene.tif")
    print(f"Generated local sample scene: {scene_path}")

    with rasterio.open(scene_path) as dataset:
        arrays = {band: dataset.read(index).astype(float) for index, band in enumerate(BANDS, start=1)}

    blue, green, red, nir = arrays["B02"], arrays["B03"], arrays["B04"], arrays["B08"]

    true_rgb = np.dstack([_stretch(red), _stretch(green), _stretch(blue)])
    Image.fromarray(true_rgb, mode="RGB").save(OUTPUT_TRUE_COLOR)

    false_rgb = np.dstack([_stretch(nir), _stretch(red), _stretch(green)])
    Image.fromarray(false_rgb, mode="RGB").save(OUTPUT_FALSE_COLOR)

    nir_gray = _stretch(nir)
    Image.fromarray(nir_gray, mode="L").save(OUTPUT_NIR)

    metadata = {
        "item_id": "local-sample-scene",
        "acquisition_datetime": datetime.now(timezone.utc).isoformat(),
        "cloud_cover_pct": 0.0,
        "platform": "synthetic-demo",
        "bbox": None,
        "views": {
            "true_color": {
                "file": "eyes_true_color_demo.png",
                "bands": "B04->R, B03->G, B02->B",
                "label": "True color -- what the human eye would see",
            },
            "false_color": {
                "file": "eyes_false_color_demo.png",
                "bands": "B08->R, B04->G, B03->B",
                "label": "False color (NIR) -- vegetation and bloom signal, invisible to the eye",
            },
            "nir": {
                "file": "eyes_nir_demo.png",
                "bands": "B08 (842nm) grayscale",
                "label": "Raw near-infrared, 842nm -- a single band the eye cannot perceive at all",
            },
        },
        "caption": (
            f"Synthetic sample scene, generated {date.today().isoformat()} "
            "-- local fallback, not a live or real satellite fetch"
        ),
    }
    OUTPUT_META.write_text(json.dumps(metadata, indent=2))
    print(f"Saved scene metadata to {OUTPUT_META}")
    print("\nDone. Three views ready for the EYES band toggle:")
    print("  true color / false color / raw NIR")


if __name__ == "__main__":
    main()