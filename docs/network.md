# Optional water-network analysis

## Ten-module map and implementation status

Freshwater Sentinel is tracked against this exact ten-module map:

| Module | Implementation status |
| --- | --- |
| EYES | Implemented — scene ingestion, STAC discovery, and spectral observation inputs. |
| MEMORY | Implemented — in-memory scene registry and persisted demo histories. |
| BRAIN | Implemented — spectral features, rainfall fusion, quality proxies, and risk scoring. |
| SENTINEL | Implemented — Sentinel-2 COG loading with acquisition provenance. |
| NETWORK | Implemented — deterministic water-point graph construction and propagation. |
| DECISION | Implemented — `/network/analyze` selects one top-ranked node as `decision.act_here`, with deterministic rationale and alternatives. |
| VOICE | Implemented — plain-language explanations and voice-oriented response content. |
| HANDS | Implemented — field-task and alert-oriented operational routes. |
| VERIFY | Implemented — evidence-aware safety handling and verification helpers. |
| MEMORY 2.0 | In progress — durable, feedback-aware memory is not yet complete. |

## Graph construction

Phase 1 builds a deterministic graph from injected records or the committed `data/malawi_boreholes.csv` fixture. WPDx- and OpenWashData-shaped rows are accepted through `records_from_optional_source`; no live download is needed for the graph builder.

Safety is fail-closed: missing or incomplete safety/lab evidence is `FIELD SAMPLE REQUIRED`. A source is never marked safe merely because it appears in a fixture.

## OneAquaHealth ecosystem adapter

`app/oah_ecosystem.py` provides an optional, read-only adapter for the public OneAquaHealth research ecosystem dashboard:

- **GET endpoint:** `https://api.enora-oah.eu/api/dashboards/city`
- **Authentication:** none; no API key or account is required.
- **Coverage:** city/research-site dashboard records from European OneAquaHealth research sites.
- **Coordinates:** the city endpoint does not provide coordinates. Normalized records retain nullable `latitude`/`longitude` fields and do not invent a location. Such records are useful for provenance and ecosystem discovery, but cannot be used as geospatial network nodes until a separately verified location is supplied.
- **Provenance:** normalized nodes are tagged `source="oneaquahealth"`, carry the exact endpoint URL, and include a UTC fetch timestamp.
- **Limits:** this is a public dashboard feed rather than a guaranteed stable analytical API. Its schema, availability, completeness, update cadence, pagination, and rate limits may change. The adapter uses bounded request timeouts, validates records with Pydantic, and degrades to an empty unsuccessful snapshot on transport/JSON failure. It does not claim live data when a request fails.

Run the live fetch explicitly when network access is intended:

```bash
python scripts/fetch_oah_ecosystem.py
```

The script writes `data/oah_ecosystem.json` and merges only the OneAquaHealth provenance entry into `data/manifest.json`; existing manifest entries are retained. Tests use mocked responses and do not contact the live endpoint.

## Analysis and decision response

`POST /network/build` remains deterministic and `POST /network/analyze` returns propagation, uncertainty, safe alternatives, and the dashboard payload. It also returns this additive field without removing any existing fields:

```json
{
  "decision": {
    "act_here": "node-id",
    "rationale": "Prioritize node-id: ...",
    "alternatives": []
  }
}
```

`decision.act_here` is selected by descending propagated risk score, then ascending hop count, then node ID. This tie-breaking keeps repeated analyses stable. `decision.alternatives` uses the same explicit-lab-supported safe alternatives already returned at the top level.

Phase 2 provides `app.verification.grade_alerts` for injected dated cholera cases, `AlertMemory` for JSON feedback history, and `scripts/backtest.py`. These components do not fabricate WHO data or Sentinel downloads.
