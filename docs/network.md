# Optional water-network analysis

Phase 1 builds a deterministic graph from injected records or the committed `data/malawi_boreholes.csv` fixture. WPdx and OpenWashData-shaped rows are accepted through `records_from_optional_source`; no live download is performed.

Safety is fail-closed: missing or incomplete safety/lab evidence is `FIELD SAMPLE REQUIRED`. A source is never marked safe merely because it appears in a fixture. A safe alternative requires an explicit safe result plus `turbidity_ntu` and `faecal_coli_count` evidence.

`POST /network/build` returns the graph. `POST /network/analyze` returns propagation, uncertainty, safe alternatives, and a dashboard payload. Phase 2 provides `app.verification.grade_alerts` for injected dated cholera cases, `AlertMemory` for JSON feedback history, and `scripts/backtest.py`. These components do not fabricate WHO data or Sentinel downloads.

Examples: `python scripts/demo_network_alert.py`; `python scripts/build_water_network.py --output network.json`; `python scripts/backtest.py --alerts alerts.json --cases cases.json`.
