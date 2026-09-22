"""Generate a tiny multispectral GeoTIFF for local demos and tests."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

BANDS = ("B02", "B03", "B04", "B05", "B08", "B11")


def create_sample_scene(output: str | Path = "data/sample_scene.tif") -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    size = 64
    y, x = np.mgrid[0:size, 0:size]
    bloom = (((x - 32) ** 2 + (y - 31) ** 2) < 15**2).astype(np.float32)
    values = {
        "B02": 0.045 + 0.010 * bloom,
        "B03": 0.160 + 0.055 * bloom,
        "B04": 0.060 + 0.012 * bloom,
        # The bloom patch raises green reflectance more than red-edge,
        # producing a higher NDCI/chlorophyll signal than surrounding water.
        "B05": 0.110 + 0.035 * bloom,
        "B08": 0.105 + 0.020 * bloom,
        "B11": 0.030 + 0.006 * bloom,
    }
    profile = {
        "driver": "GTiff",
        "height": size,
        "width": size,
        "count": len(BANDS),
        "dtype": "float32",
        "crs": "EPSG:4326",
        "transform": from_origin(36.8219, -1.2864, 0.0001, 0.0001),
        "compress": "deflate",
    }
    with rasterio.open(path, "w", **profile) as dataset:
        for index, band in enumerate(BANDS, start=1):
            dataset.write(values[band].astype(np.float32), index)
        dataset.descriptions = BANDS
        dataset.update_tags(ACQUISITION_DATE=date.today().isoformat())
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/sample_scene.tif")
    args = parser.parse_args()
    print(create_sample_scene(args.output))


if __name__ == "__main__":
    main()
