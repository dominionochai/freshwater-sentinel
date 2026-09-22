#!/usr/bin/env python3
"""Build the checked-in Malawi slice of the HDX WPDx Enhanced resource."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = "https://data.humdata.org/dataset/4c5e7cd0-3d28-4827-888c-e58e80b2eb47/resource/d0a23110-8be3-43f2-ab31-44a37cb5b804/download/wpdx_enhanced.csv"
DATASET_ID = "4c5e7cd0-3d28-4827-888c-e58e80b2eb47"
RESOURCE_ID = "d0a23110-8be3-43f2-ab31-44a37cb5b804"
OUTPUT_COLUMNS = ["row_id", "water_source", "water_tech", "country_code", "lat_deg", "lon_deg", "status_id", "report_date", "install_year"]
LICENSE = "Creative Commons Attribution Share-Alike"
MALAWI_BBOX = (-17.2, -9.3, 32.6, 35.9)

ALIASES = {
    "row_id": ("row_id", "water_point_id", "waterpoint_id", "wpdx_id", "source_id", "id"),
    "water_source": ("water_source", "source", "waterpoint_type", "water_point_type"),
    "water_tech": ("water_tech", "technology", "water_point_technology", "tech"),
    "country_code": ("country_code", "country_iso3", "iso3", "iso_3", "clean_country_id"),
    "country": ("country", "country_name", "country_name_en", "country_label"),
    "lat_deg": ("lat_deg", "latitude", "lat", "gps_latitude"),
    "lon_deg": ("lon_deg", "longitude", "lon", "gps_longitude"),
    "status_id": ("status_id", "status", "water_point_status", "functionality_status"),
    "report_date": ("report_date", "date", "last_seen", "data_date", "install_date"),
    "install_year": ("install_year", "year_installed", "installation_year", "year"),
}


def _normalise_header(value: str) -> str:
    value = value.strip().lstrip("#").lower()
    return re.sub(r"[^a-z0-9]+", "_", value).strip("_")


def _resolve_headers(fieldnames: list[str]) -> dict[str, str | None]:
    by_normalised = {_normalise_header(name): name for name in fieldnames}
    return {
        output_name: next((by_normalised[_normalise_header(candidate)] for candidate in candidates if _normalise_header(candidate) in by_normalised), None)
        for output_name, candidates in ALIASES.items()
    }


def _cell(row: dict[str, str], column: str | None) -> str:
    return (row.get(column, "") if column else "").strip()


def _number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_malawi(row: dict[str, str], headers: dict[str, str | None]) -> bool:
    country_code_column = headers["country_code"]
    if country_code_column:
        return _cell(row, country_code_column).upper() == "MWI"
    country_column = headers["country"]
    if country_column:
        value = _cell(row, country_column).casefold()
        return value in {"mwi", "malawi"} or value.startswith("malawi ")
    lat = _number(_cell(row, headers["lat_deg"]))
    lon = _number(_cell(row, headers["lon_deg"]))
    if lat is None or lon is None:
        return False
    min_lat, max_lat, min_lon, max_lon = MALAWI_BBOX
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def build(input_path: Path, output_path: Path, manifest_path: Path) -> tuple[int, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with input_path.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        fieldnames = list(reader.fieldnames or [])
        if not fieldnames:
            raise ValueError("HDX resource has no CSV header")
        headers = _resolve_headers(fieldnames)
        if headers["country_code"]:
            filter_method = f"{headers['country_code']} == MWI"
        elif headers["country"]:
            filter_method = f"{headers['country']} == Malawi (or MWI)"
        else:
            filter_method = "Malawi bounding box: lat -17.2..-9.3, lon 32.6..35.9"
        with output_path.open("w", newline="", encoding="utf-8") as destination:
            writer = csv.DictWriter(destination, fieldnames=OUTPUT_COLUMNS, lineterminator="\n")
            writer.writeheader()
            for source_row_number, row in enumerate(reader, start=2):
                if not any((value or "").strip() for value in row.values()) or not _is_malawi(row, headers):
                    continue
                output_row = {column: _cell(row, headers.get(column)) for column in OUTPUT_COLUMNS}
                if not output_row["row_id"]:
                    output_row["row_id"] = f"wpdx-{source_row_number}"
                writer.writerow(output_row)
                count += 1
    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    manifest = {
        "dataset_id": DATASET_ID,
        "resource_id": RESOURCE_ID,
        "title": "Water Point Data Exchange (WPDx) Enhanced",
        "source_url": SOURCE_URL,
        "license": LICENSE,
        "downloaded_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "country": "Malawi",
        "country_code": "MWI",
        "filter": filter_method,
        "source_columns": fieldnames,
        "columns": OUTPUT_COLUMNS,
        "rows": count,
        "sha256": digest,
        "truncated": False,
        "notes": "No truncation applied; all matching Malawi rows were emitted.",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return count, digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/wpdx_malawi.csv"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.json"))
    args = parser.parse_args()
    count, digest = build(args.input, args.output, args.manifest)
    print(f"Wrote {args.output}: rows={count} sha256={digest}")


if __name__ == "__main__":
    main()
