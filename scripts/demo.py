"""Run the complete local ingest -> analyze -> human alert flow."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# `python scripts/demo.py` puts `scripts/` (not the repository root) on
# sys.path. Add the root so the sibling script can be imported as documented.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import httpx

from scripts.make_sample_scene import create_sample_scene


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--language", choices=("en", "sw"), default="en")
    args = parser.parse_args()

    scene_path = create_sample_scene(Path("data/sample_scene.tif"))
    with httpx.Client(base_url=args.base_url, timeout=30.0) as client:
        ingest = client.post(
            "/ingest",
            json={
                "water_body_id": "demo-lake",
                "scene_path": str(scene_path),
                "acquisition_date": "2026-01-15",
            },
        )
        ingest.raise_for_status()
        scene_id = ingest.json()["scene_id"]
        analysis = client.post(
            "/analyze",
            json={
                "scene_id": scene_id,
                "community_profile": {
                    "name": "Demo Lake community",
                    "language": args.language,
                    "preferred_channel": "dashboard",
                    "children": [{"age_group": "under_10", "count": 14}],
                    "school": "Demo Lake Primary School",
                    "pets": [{"households_with_pets": 3}],
                },
            },
        )
        analysis.raise_for_status()
        payload = analysis.json()

    print(payload["human_alert"]["title"])
    print(payload["human_alert"]["message"])
    print(payload["human_alert"]["action"])


if __name__ == "__main__":
    main()
