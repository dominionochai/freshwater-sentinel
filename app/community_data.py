"""Load privacy-preserving community profile seed data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.models import CommunityProfile


_PROFILE_PATH = Path(__file__).resolve().parents[1] / "data" / "community_profiles.json"


def load_community_profiles() -> list[dict[str, Any]]:
    """Return checked-in community profile seed records with a canonical name."""
    with _PROFILE_PATH.open(encoding="utf-8") as profile_file:
        profiles = json.load(profile_file)
    if not isinstance(profiles, list):
        raise ValueError("community profile seed data must be a list")

    normalized: list[dict[str, Any]] = []
    for index, record in enumerate(profiles):
        if not isinstance(record, dict):
            raise ValueError(f"community profile at index {index} must be an object")

        profile = dict(record)
        names = profile.get("names", [])
        if isinstance(names, str):
            names = [names]
        if not isinstance(names, list) or not all(isinstance(value, str) for value in names):
            raise ValueError(f"community profile at index {index} has invalid names")
        names = [value.strip() for value in names if value.strip()]

        candidates = [profile.get("name"), *names, profile.get("community")]
        canonical_name = next(
            (value.strip() for value in candidates if isinstance(value, str) and value.strip()),
            None,
        )
        if canonical_name is None:
            raise ValueError(f"community profile at index {index} must have a meaningful name")

        profile["name"] = canonical_name
        # Keep the legacy display-name collection available to existing clients.
        profile["names"] = names or [canonical_name]
        normalized.append(profile)

    return normalized


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
            children=[{"age_group": "under_10", "count": 14}],
            school="Demo Lake Primary School",
            pets=[{"households_with_pets": 3}],
        )
    return CommunityProfile(**record)
