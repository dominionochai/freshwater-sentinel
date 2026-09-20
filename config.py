"""Central, reviewable configuration for the screening pipeline."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_SCENE_PATH = DATA_DIR / "sample_scene.tif"

# Water mask thresholds.
MNDWI_MIN = 0.05
NDVI_MAX_FOR_WATER = 0.45
REFLECTANCE_MIN = 0.0
REFLECTANCE_MAX = 1.0

# Screening proxy breakpoints; these are not regulatory limits.
TURBIDITY_YELLOW_NTU = 25.0
TURBIDITY_RED_NTU = 60.0
CHLOROPHYLL_YELLOW_UG_L = 20.0
CHLOROPHYLL_RED_UG_L = 50.0
MIN_ANALYZED_PIXELS = 10

# Activity-specific normalized thresholds, intentionally easy to audit/change.
RISK_THRESHOLDS = {
    "swimming": {"yellow": 0.35, "red": 0.65},
    "fishing": {"yellow": 0.45, "red": 0.72},
    "pets": {"yellow": 0.30, "red": 0.58},
}
ACTIVITY_WEIGHTS = {
    "swimming": {"turbidity": 0.35, "chlorophyll": 0.45, "observations": 0.20},
    "fishing": {"turbidity": 0.25, "chlorophyll": 0.45, "observations": 0.30},
    "pets": {"turbidity": 0.25, "chlorophyll": 0.55, "observations": 0.20},
}
