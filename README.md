# Freshwater Sentinel

Freshwater Sentinel is a backend-first prototype for transparent freshwater
screening. It combines water-only multispectral proxies with synthetic,
privacy-preserving community and clinic-demo records. The health linkage is an
exploratory screening aid: it does not diagnose patients, establish disease
transmission, or replace field and laboratory confirmation.

## Included

- A FastAPI service in `app/main.py` with `/ingest`, `/analyze`,
  `/risk/{water_body_id}`, `/health`, `/community-profiles`, and the synthetic
  `/health-linkage` endpoint.
- Validated Pydantic request, response, and provenance models in
  `app/models.py`.
- Deterministic offline GeoTIFF generation with
  `scripts/make_sample_scene.py` and an end-to-end local demo in
  `scripts/demo.py`.
- Public Earth Search STAC discovery and Sentinel-2 COG loading in
  `app/earth_search.py`, with provenance retained on every loaded scene.
- Water masking, transparent quality proxies, activity-risk scoring, and
  plain-language explanations. These are screening proxies and require local
  calibration and validation.

## Quickstart

Python 3.11 or newer is recommended:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python scripts/make_sample_scene.py --output data/sample_scene.tif
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is
at `/docs`. To run the deterministic offline demo instead:

```bash
python scripts/demo.py
```

## API flow

The normal local flow is:

```text
POST /ingest -> in-memory scene registry
POST /analyze -> water mask -> quality metrics -> activity risk -> explanation
GET  /risk/{water_body_id} -> latest analysis for that water body
```

`/ingest` accepts exactly one of these scene sources:

- `scene`: an inline JSON payload with acquisition date and B02/B03/B04/B05/B08/B11 arrays;
- `scene_path`: a local GeoTIFF containing those six bands; or
- `stac_item_url`: an HTTPS Earth Search Sentinel-2 L2A STAC item URL.

For example, after starting the service:

```bash
curl -X POST http://127.0.0.1:8000/ingest \\
  -H 'content-type: application/json' \\
  -d '{
    "water_body_id": "lake-demo",
    "stac_item_url": "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/ITEM_ID"
  }'
```

The response contains a generated `scene_id`, acquisition date, source, and
sanitized provenance metadata. Pass that `scene_id` to `/analyze`.

## Fetch a public Sentinel-2 scene

`fetch_s2_scene.py` searches the public Earth Search API, selects the first
matching Sentinel-2 L2A item, loads its six required COG assets, and writes a
local six-band GeoTIFF. The output tags include the source, item ID/assets,
acquisition date, and water-body ID.

```bash
python scripts/fetch_s2_scene.py \\
  --bbox 36.70 -1.35 36.95 -1.15 \\
  --datetime 2025-01-01/2025-12-31 \\
  --cloud-cover 20 \\
  --output data/sentinel2_scene.tif
```

The script uses only the public Earth Search STAC endpoint by default; use
`--endpoint` and `--timeout` when pointing at a compatible service. Network
failures, malformed STAC records, missing bands, and invalid acquisition dates
are reported instead of silently creating synthetic data. No API key is
required for the public endpoint.

## Data and scientific boundaries

The checked-in `data/clinic_reports.json` and `data/community_profiles.json`
files are synthetic/demo records and contain no patient identifiers.
`data/malawi_boreholes.csv` is a filtered borehole seed; see `data/README.md`
for source and licence notes. The sample GeoTIFF is deterministic (NumPy seed
7), so offline tests and demos are reproducible.

Clouds, atmospheric correction, adjacency effects, sensor differences,
shallow bottoms, mixed pixels, and local ecology can bias the proxies. NDCI
and chlorophyll-a estimates require local calibration. Human and community
review remains part of the operating model.

## Development

```bash
python -m compileall app scripts config.py vendor
pytest -q
ruff check .
```

## Attribution and licence

Project code is MIT-licensed under `LICENSE`. External component-level
provenance and usage boundaries are documented in `vendor/README.md`. The
borehole extract retains its CC BY 4.0 attribution in `data/README.md`.
