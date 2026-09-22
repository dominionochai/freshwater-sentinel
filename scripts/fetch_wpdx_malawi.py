#!/usr/bin/env python3
"""Build the checked-in Malawi slice of the HDX WPDx Enhanced resource."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

SOURCE_URL = "https://data.humdata.org/dataset/4c5e7cd0-3d28-4827-888c-e58e80b2eb47/resource/d0a23110-8be3-43f2-ab31-44a37cb5b804/download/wpdx_enhanced.csv"
DATASET_ID = "4c5e7cd0-3d28-4827-888c-e58e80b2eb47"
RESOURCE_ID = "d0a23110-8be3-43f2-ab31-44a37cb5b804"
OUTPUT_COLUMNS = [
    "row_id",
    "water_source",
    "water_tech",
    "country_code",
    "lat_deg",
    "lon_deg",
    "status_id",
    "report_date",
    "install_year",
]


def build(input_path: Path, output_path: Path, manifest_path: Path) -> tuple[int, str]:
    """Filter the source with csv.DictReader and emit the stable nine-column slice."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with input_path.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        fieldnames = set(reader.fieldnames or [])
        required = set(OUTPUT_COLUMNS) | {"clean_country_id"}
        missing = sorted(required - fieldnames)
        if missing:
            raise ValueError(f"HDX resource is missing required columns: {', '.join(missing)}")

        with output_path.open("w", newline="", encoding="utf-8") as destination:
            writer = csv.DictWriter(
                destination,
                fieldnames=OUTPUT_COLUMNS,
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writeheader()
            for row in reader:
                if (row.get("clean_country_id") or "").strip() != "MWI":
                    continue
                writer.writerow({column: row.get(column) or "" for column in OUTPUT_COLUMNS})
                count += 1

    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    manifest = {
        "dataset_id": DATASET_ID,
        "resource_id": RESOURCE_ID,
        "title": "Water Point Data Exchange (WPDx) Enhanced",
        "source_url": SOURCE_URL,
        "license": "Creative Commons Attribution Share-Alike",
        "country": "Malawi",
        "country_code": "MWI",
        "filter": "clean_country_id == MWI",
        "columns": OUTPUT_COLUMNS,
        "count": count,
        "sha256": digest,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return count, digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/wpdx_malawi.csv"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.json"))
    args = parser.parse_args()
    count, digest = build(args.input, args.output, args.manifest)
    print(f"Wrote {args.output}: count={count} sha256={digest}")


if __name__ == "__main__":
    main()
