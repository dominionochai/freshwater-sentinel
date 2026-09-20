"""Create a deterministic Sentinel-2-like multiband GeoTIFF for offline demos."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

BANDS = ("B02", "B03", "B04", "B08", "B11", "B12")


def make_scene(size: int = 64) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:size, 0:size]
    water = ((xx - size / 2) / (size * 0.39)) ** 2 + ((yy - size / 2) / (size * 0.30)) ** 2 < 1.0
    base = {name: np.full((size, size), value, dtype="float32") for name, value in {"B02": 0.18, "B03": 0.16, "B04": 0.20, "B08": 0.32, "B11": 0.17, "B12": 0.14}.items()}
    gradient = (xx + yy) / max(2 * size, 1)
    base["B02"][water] = 0.055 + 0.008 * gradient[water]
    base["B03"][water] = 0.105 + 0.025 * gradient[water]
    base["B04"][water] = 0.075 + 0.020 * gradient[water]
    base["B08"][water] = 0.115 + 0.020 * gradient[water]
    base["B11"][water] = 0.045 + 0.010 * gradient[water]
    base["B12"][water] = 0.035 + 0.008 * gradient[water]
    for name in BANDS:
        base[name] = np.clip(base[name] + rng.normal(0.0, 0.002, (size, size)), 0.0, 1.0).astype("float32")
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/sample_scene.tif"))
    parser.add_argument("--size", type=int, default=64)
    args = parser.parse_args()
    if args.size < 16:
        parser.error("--size must be at least 16")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bands = make_scene(args.size)
    with rasterio.open(args.output, "w", driver="GTiff", height=args.size, width=args.size, count=len(BANDS), dtype="float32", crs="EPSG:4326", transform=from_origin(-1.0, 1.0, 0.001, 0.001)) as dataset:
        dataset.update_tags(ACQUISITION_DATE="2026-09-20")
        for index, name in enumerate(BANDS, start=1):
            dataset.set_band_description(index, name)
            dataset.write(bands[name], index)
    print(f"wrote deterministic sample scene to {args.output}")


if __name__ == "__main__":
    main()
