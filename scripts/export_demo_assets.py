#!/usr/bin/env python3
"""Build the offline demo assets from the repository's real analysis pipeline.

This script intentionally does not download data, call a service, or require an
API key.  It is a generator: run it locally when demo assets are needed.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable

# ``python scripts/export_demo_assets.py`` puts ``scripts/`` on sys.path first.
# Add the repository root so the real ``app`` package and scene generator are
# imported consistently from both the repository root and an installed checkout.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
from PIL import Image
import rasterio

from app.alerts import build_human_alert
from app.community_data import load_community_profiles
from app.models import CommunityProfile, HABObservation
from app.pipeline import analyze, scene_from_geotiff
from app.water_masking import create_water_mask
from scripts.make_sample_scene import create_sample_scene


DEMO_COMMUNITY = "Demo Lake community"
ASSET_DIR = REPO_ROOT / "assets"
SCENE_PATH = REPO_ROOT / "data" / "sample_scene.tif"


def _status(label: str, action: Callable[[], Any]) -> Any:
    """Run one export step with a clear success/failure status."""
    print(f"[demo-export] {label} ...", flush=True)
    try:
        result = action()
    except Exception as exc:
        print(f"[demo-export] {label} FAILED: {exc}", flush=True)
        raise
    print(f"[demo-export] {label} OK", flush=True)
    return result


def _stretch_2_98(values: np.ndarray) -> np.ndarray:
    """Percentile-stretch one band to uint8 using the requested 2-98 range."""
    values = np.asarray(values, dtype=np.float32)
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return np.zeros(values.shape, dtype=np.uint8)
    low, high = np.percentile(finite, (2, 98))
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        return np.zeros(values.shape, dtype=np.uint8)
    scaled = (values - low) / (high - low)
    return np.clip(np.nan_to_num(scaled, nan=0.0), 0.0, 1.0).mul(255) if False else (np.clip(np.nan_to_num(scaled, nan=0.0), 0.0, 1.0) * 255).astype(np.uint8)


def _read_named_bands(path: Path) -> dict[str, np.ndarray]:
    """Read bands by the GeoTIFF descriptions emitted by make_sample_scene."""
    with rasterio.open(path) as dataset:
        descriptions = [description.upper() if description else "" for description in dataset.descriptions]
        fallback = ("B02", "B03", "B04", "B05", "B08", "B11")
        names = [description or fallback[index] for index, description in enumerate(descriptions)]
        return {
            name: dataset.read(index + 1).astype(np.float32)
            for index, name in enumerate(names)
        }


def _write_visual_assets() -> dict[str, Any]:
    bands = _read_named_bands(SCENE_PATH)
    required = ("B02", "B03", "B04", "B08")
    missing = [name for name in required if name not in bands]
    if missing:
        raise ValueError(f"sample scene is missing required bands: {', '.join(missing)}")

    stretched = {name: _stretch_2_98(bands[name]) for name in required}
    rgb = np.dstack((stretched["B04"], stretched["B03"], stretched["B02"]))
    Image.fromarray(rgb, mode="RGB").save(ASSET_DIR / "rgb_composite.png")

    nir = stretched["B08"]
    nir_rgb = np.dstack((nir, nir, nir))
    Image.fromarray(nir_rgb, mode="RGB").save(ASSET_DIR / "b08_nir_composite.png")

    water_mask, diagnostics = create_water_mask(bands, use_omniwatermask=False)
    mask = np.asarray(water_mask, dtype=bool)
    dimmed_land = np.clip(rgb.astype(np.float32) * 0.38, 0, 255).astype(np.uint8)
    overlay = np.where(mask[..., None], np.array([0x5F, 0xB8, 0xA8], dtype=np.uint8), dimmed_land)
    Image.fromarray(overlay.astype(np.uint8), mode="RGB").save(ASSET_DIR / "water_mask_overlay.png")

    return {
        "band_order": ["B04", "B03", "B02"],
        "nir_band": "B08",
        "stretch": "2-98 percentile per band",
        "water_color": "#5fb8a8",
        "non_water_factor": 0.38,
        "mask_diagnostics": diagnostics,
        "water_pixels": int(mask.sum()),
        "scene_pixels": int(mask.size),
    }


def _model_dump(value: Any) -> Any:
    """Serialize Pydantic models, dataclasses, dates, numpy values, and maps."""
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump(mode="json")
        except TypeError:
            return value.model_dump()
    if hasattr(value, "dict") and callable(value.dict):
        return value.dict()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {str(key): _model_dump(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_model_dump(item) for item in value]
    if isinstance(value, (date,)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return value.item()
    return value


def _demo_profile() -> CommunityProfile:
    """Use a checked-in profile when present, otherwise the real model default."""
    profiles = load_community_profiles()
    record = next(
        (
            item
            for item in profiles
            if item.get("name") == DEMO_COMMUNITY or item.get("community") == DEMO_COMMUNITY
        ),
        None,
    )
    if record is None:
        return CommunityProfile(
            names=[DEMO_COMMUNITY],
            community=DEMO_COMMUNITY,
            name=DEMO_COMMUNITY,
            language="en",
            preferred_channel="dashboard",
        )
    return CommunityProfile(**record)


def _write_analysis_asset() -> dict[str, Any]:
    scene = scene_from_geotiff("demo-lake", str(SCENE_PATH), requested_date=date.today())
    observations = [
        HABObservation(
            source="offline-demo-observation",
            observed_on=date.today(),
            severity=0.0,
            note="Synthetic demonstration observation; confirm with field sampling.",
        )
    ]
    result = analyze(scene, observations)
    profile_en = _demo_profile()
    profile_sw = CommunityProfile(
        **{
            **_model_dump(profile_en),
            "language": "sw",
            "name": DEMO_COMMUNITY,
            "community": DEMO_COMMUNITY,
        }
    )
    risk = result.risk
    result_json = _model_dump(result)
    risk_json = _model_dump(risk)
    result_json["risk_scores"] = {
        activity: {"score": values["score"], "tier": values["label"], "rationale": values["rationale"]}
        for activity, values in risk_json.items()
    }
    result_json["alerts"] = {
        "en": _model_dump(build_human_alert(risk, profile_en)),
        "sw": _model_dump(build_human_alert(risk, profile_sw)),
    }
    result_json["community_profile"] = {
        "name": DEMO_COMMUNITY,
        "english": _model_dump(profile_en),
        "swahili": _model_dump(profile_sw),
    }
    result_json["observations"] = _model_dump(observations)
    result_json["export_notes"] = {
        "offline": True,
        "pipeline": "scene_from_geotiff -> analyze(scene, observations)",
        "uncertainty_source": "analysis.explanation.uncertainty and analysis.quality.quality_uncertainty",
        "explainability_source": "analysis.explanation",
    }
    with (ASSET_DIR / "analysis.json").open("w", encoding="utf-8") as output:
        json.dump(result_json, output, indent=2, ensure_ascii=False, sort_keys=True)
        output.write("\n")
    return result_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--asset-dir",
        type=Path,
        default=ASSET_DIR,
        help="directory for PNG and JSON outputs (default: assets)",
    )
    args = parser.parse_args()
    global ASSET_DIR
    ASSET_DIR = args.asset_dir if args.asset_dir.is_absolute() else REPO_ROOT / args.asset_dir
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    _status("create data/sample_scene.tif", lambda: create_sample_scene(SCENE_PATH))
    _status("write RGB, B08, and water-mask overlay assets", _write_visual_assets)
    _status("write full pipeline analysis and bilingual alerts", _write_analysis_asset)
    print(f"[demo-export] assets written under {ASSET_DIR}", flush=True)


if __name__ == "__main__":
    main()
