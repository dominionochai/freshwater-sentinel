from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

import requests

from app.oah_ecosystem import OAH_ECOSYSTEM_URL, fetch_oah_ecosystem, normalize_records


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_fetch_normalizes_mocked_city_payload_without_network(monkeypatch):
    calls = []

    def fake_get(url, *, timeout):
        calls.append((url, timeout))
        return FakeResponse({"data": [{"id": "site-1", "city": "Coimbra", "country": "Portugal", "status": "active"}, {"city_id": 2, "name": "Research site", "municipality": "Ghent"}]})

    monkeypatch.setattr("app.oah_ecosystem.requests.get", fake_get)
    result = fetch_oah_ecosystem(timeout=3.5)

    assert result.ok is True
    assert calls == [(OAH_ECOSYSTEM_URL, 3.5)]
    assert [record.node_id for record in result.records] == ["site-1", "2"]
    assert result.nodes[0].source == "oneaquahealth"
    assert result.nodes[0].source_url == OAH_ECOSYSTEM_URL
    assert result.nodes[0].latitude is None
    assert result.nodes[0].longitude is None
    assert result.nodes[0].fetched_at_utc.tzinfo == timezone.utc


def test_request_failure_degrades_to_empty_result(monkeypatch):
    def fail(*args, **kwargs):
        raise requests.Timeout("offline in test")

    monkeypatch.setattr("app.oah_ecosystem.requests.get", fail)
    result = fetch_oah_ecosystem()

    assert result.ok is False
    assert result.records == []
    assert result.nodes == []
    assert "Timeout" in (result.error or "")


def test_normalize_accepts_single_record_and_pydantic_models():
    records = normalize_records({"id": "x", "label": "European site", "country_name": "France"})
    assert len(records) == 1
    assert records[0].node_id == "x"
    assert records[0].name == "European site"
    assert records[0].country == "France"


def test_script_writes_snapshot_and_preserves_manifest(tmp_path: Path):
    script_path = Path(__file__).parents[1] / "scripts" / "fetch_oah_ecosystem.py"
    spec = importlib.util.spec_from_file_location("fetch_oah_ecosystem_script", script_path)
    assert spec and spec.loader
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)

    fetched_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    mocked = script.OAHFetchResult(fetched_at_utc=fetched_at, ok=True, records=normalize_records([{"id": "site-1", "city": "Lyon"}]), nodes=[])
    output = tmp_path / "data" / "oah_ecosystem.json"
    manifest = tmp_path / "data" / "manifest.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps({"provenance": {"existing": {"keep": True}}, "other": "untouched"}), encoding="utf-8")

    script.write_snapshot(mocked, output, manifest)

    written = json.loads(output.read_text(encoding="utf-8"))
    written_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    assert written["records"][0]["node_id"] == "site-1"
    assert written["source_url"] == OAH_ECOSYSTEM_URL
    assert written_manifest["provenance"]["existing"] == {"keep": True}
    assert written_manifest["provenance"]["oneaquahealth"]["auth"] == "none"
    assert written_manifest["other"] == "untouched"
