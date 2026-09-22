# Optional water-network analysis

Phase 1 builds a deterministic graph from injected records or the committed
`data/malawi_boreholes.csv` fixture. WPdx and OpenWashData-shaped rows are
accepted through `records_from_optional_source`; no live download is needed
for the graph builder.

Safety is fail-closed: missing or incomplete safety/lab evidence is
`FIELD SAMPLE REQUIRED`. A source is never marked safe merely because it
appears in a fixture.

## OneAquaHealth ecosystem adapter

`app/oah_ecosystem.py` provides an optional, read-only adapter for the public
OneAquaHealth research ecosystem dashboard:

- **GET endpoint:** `https://api.enora-oah.eu/api/dashboards/city`
- **Authentication:** none; no API key or account is required.
- **Coverage:** city/research-site dashboard records from European
  OneAquaHealth research sites.
- **Coordinates:** the city endpoint does not provide coordinates. The
  normalized records therefore retain nullable `latitude`/`longitude` fields
  and do not invent a location. Such records are useful for provenance and
  ecosystem discovery, but cannot be used as geospatial network nodes until a
  separately verified location is supplied.
- **Provenance:** normalized nodes are tagged `source="oneaquahealth"`, carry
  the exact endpoint URL, and include a UTC fetch timestamp.
- **Limits:** this is a public dashboard feed rather than a guaranteed stable
  analytical API. Its schema, availability, completeness, update cadence,
  pagination, and rate limits may change. The adapter uses a bounded
  `requests` timeout, validates records with Pydantic, and degrades to an
  empty unsuccessful snapshot on transport/JSON failures. It does not claim
  live data when a request fails.

Run the live fetch explicitly when network access is intended:

```bash
python scripts/fetch_oah_ecosystem.py
```

The script writes `data/oah_ecosystem.json` and merges only the
OneAquaHealth provenance entry into `data/manifest.json`; existing manifest
entries are retained. Tests use mocked responses and do not contact the live
endpoint.

`POST /network/build` remains deterministic and `POST /network/analyze`
returns propagation, uncertainty, safe alternatives, and a dashboard payload.
Phase 2 provides `app.verification.grade_alerts` for injected dated cholera
cases, `AlertMemory` for JSON feedback history, and `scripts/backtest.py`.
These components do not fabricate WHO data or Sentinel downloads.
