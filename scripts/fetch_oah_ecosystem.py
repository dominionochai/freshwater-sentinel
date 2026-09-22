"""Fetch OneAquaHealth ecosystem data into the repository data directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.oah_ecosystem import OAH_ECOSYSTEM_URL, OAHFetchResult, SOURCE, fetch_oah_ecosystem  # noqa: E402

DEFAULT_OUTPUT = ROOT / "data" / "oah_ecosystem.json"
DEFAULT_MANIFEST = ROOT / "data" / "manifest.json"


def _timestamp(result: OAHFetchResult) -> str:
    return result.fetched_at_utc.astimezone(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z")


def snapshot_payload(result: OAHFetchResult) -> dict[str, Any]:
    """Build the JSON document without fabricating records on failure."""

    payload: dict[str, Any] = {
        "source": result.source,
        "source_url": result.source_url,
        "fetched_at_utc": _timestamp(result),
        "ok": result.ok,
        "records": [record.model_dump(mode="json") for record in result.records],
        "nodes": [node.model_dump(mode="json") for node in result.nodes],
    }
    if result.error:
        payload["error"] = result.error
    return payload


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _merge_source(entries: list[Any], entry: dict[str, Any]) -> list[Any]:
    result = list(entries)
    for index, current in enumerate(result):
        if isinstance(current, dict) and (current.get("id") == SOURCE or current.get("source") == SOURCE or current.get("source_url") == OAH_ECOSYSTEM_URL):
            result[index] = entry
            return result
    result.append(entry)
    return result


def update_manifest(manifest_path: str | Path, result: OAHFetchResult) -> dict[str, Any]:
    """Update only OAH provenance and retain existing manifest content."""

    path = Path(manifest_path)
    manifest = _read_json(path)
    entry: dict[str, Any] = {
        "id": SOURCE,
        "source": SOURCE,
        "source_url": result.source_url,
        "endpoint": OAH_ECOSYSTEM_URL,
        "auth": "none",
        "path": "data/oah_ecosystem.json",
        "fetched_at_utc": _timestamp(result),
        "ok": result.ok,
        "record_count": len(result.records),
    }
    if result.error:
        entry["error"] = result.error

    provenance = manifest.get("provenance")
    if isinstance(provenance, dict):
        provenance[SOURCE] = entry
    elif isinstance(provenance, list):
        manifest["provenance"] = _merge_source(provenance, entry)
    elif provenance is None:
        manifest["provenance"] = {SOURCE: entry}
    else:
        manifest["provenance"] = {SOURCE: entry, "previous": provenance}

    if isinstance(manifest.get("sources"), list):
        manifest["sources"] = _merge_source(manifest["sources"], entry)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def write_snapshot(result: OAHFetchResult, output_path: str | Path, manifest_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot_payload(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    update_manifest(manifest_path, result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = fetch_oah_ecosystem(timeout=args.timeout)
    write_snapshot(result, args.output, args.manifest)
    print(f"wrote {args.output} ({len(result.records)} records; ok={result.ok})")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
