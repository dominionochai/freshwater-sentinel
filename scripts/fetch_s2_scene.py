"""Fetch one public Sentinel-2 scene from Earth Search as a local GeoTIFF.

The command deliberately uses the public STAC API and records the selected
scene's acquisition/provenance metadata in the output GeoTIFF tags.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

# Make ``python scripts/fetch_s2_scene.py`` work from the repository root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import rasterio

from app.earth_search import EARTH_SEARCH_URL, EarthSearchError, scene_from_earth_search
from app.pipeline import REQUIRED_BANDS, Scene


def fetch_scene(
    *,
    bbox: Sequence[float],
    datetime_range: str,
    output: str | Path,
    water_body_id: str = "earth-search-scene",
    cloud_cover: float | None = 20.0,
    endpoint: str = EARTH_SEARCH_URL,
    timeout: float = 30.0,
) -> Path:
    """Search Earth Search, load the first matching scene, and write it locally."""
    if len(bbox) != 4:
        raise ValueError("bbox must contain west, south, east, and north")
    if not 0 <= cloud_cover <= 100 if cloud_cover is not None else False:
        raise ValueError("cloud_cover must be between 0 and 100")

    scene = scene_from_earth_search(
        water_body_id=water_body_id,
        bbox=tuple(float(value) for value in bbox),
        datetime_range=datetime_range,
        cloud_cover=cloud_cover,
        endpoint=endpoint,
        timeout=timeout,
    )
    return write_scene(scene, output)


def write_scene(scene: Scene, output: str | Path) -> Path:
    """Write a loaded scene using the first COG as the spatial template."""
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    assets = scene.metadata.get("assets", {})
    template_href = assets.get(REQUIRED_BANDS[0]) if isinstance(assets, dict) else None
    if not isinstance(template_href, str) or not template_href:
        raise ValueError("scene metadata does not contain a template asset href")

    # The COG supplies CRS, transform, dimensions, and resolution.  The scene
    # arrays have already been validated and loaded by app.earth_search.
    with rasterio.open(template_href) as template:
        profile = template.profile.copy()
    profile.update(
        driver="GTiff",
        count=len(REQUIRED_BANDS),
        dtype="float32",
        compress="deflate",
        tiled=True,
    )

    with rasterio.open(destination, "w", **profile) as dataset:
        for index, band in enumerate(REQUIRED_BANDS, start=1):
            dataset.write(np.asarray(scene.bands[band], dtype=np.float32), index)
            dataset.set_band_description(index, band)
        dataset.update_tags(
            source=scene.source,
            acquisition_date=scene.acquisition_date.isoformat(),
            water_body_id=scene.water_body_id,
        )
        for key, value in scene.metadata.items():
            if isinstance(value, (str, int, float, bool)):
                dataset.update_tags(**{f"sentinel_{key}": str(value)})
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        required=True,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
        help="search bounds in WGS84 order: west south east north",
    )
    parser.add_argument(
        "--datetime",
        "--datetime-range",
        dest="datetime_range",
        required=True,
        help="STAC datetime or interval, for example 2025-01-01/2025-12-31",
    )
    parser.add_argument("--output", default="data/sentinel2_scene.tif")
    parser.add_argument("--water-body-id", default="earth-search-scene")
    parser.add_argument("--cloud-cover", type=float, default=20.0)
    parser.add_argument("--endpoint", default=EARTH_SEARCH_URL)
    parser.add_argument("--timeout", type=float, default=30.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = fetch_scene(
            bbox=args.bbox,
            datetime_range=args.datetime_range,
            output=args.output,
            water_body_id=args.water_body_id,
            cloud_cover=args.cloud_cover,
            endpoint=args.endpoint,
            timeout=args.timeout,
        )
    except (EarthSearchError, OSError, ValueError) as exc:
        parser.error(str(exc))
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
