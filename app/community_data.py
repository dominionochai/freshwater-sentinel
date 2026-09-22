"""Load privacy-preserving community profile seed data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_PROFILE_PATH = Path(__file__).resolve().parents[1] / "data" / "community_profiles.json"


def load_community_profiles() -> list[dict[str, Any]]:
    """Return the checked-in community profile seed records."""
    with _PROFILE_PATH.open(encoding="utf-8") as profile_file:
        profiles = json.load(profile_file)
    if not isinstance(profiles, list):
        raise ValueError("community profile seed data must be a list")
    return profiles
