# Freshwater Sentinel

Freshwater Sentinel is a backend-first prototype for transparent freshwater screening. It combines water-only multispectral proxies with synthetic, privacy-preserving community and clinic-demo records. The health linkage is an exploratory screening aid: it does not diagnose patients, establish disease transmission, or replace field and laboratory confirmation.

## Included

- A FastAPI service in `app/main.py` with `/ingest`, `/analyze`, `/risk/{water_body_id}`, `/health`, `/community-profiles`, and `/health-linkage` endpoints.
- Validated Pydantic request, response, and provenance models.
- Deterministic offline GeoTIFF generation and a local end-to-end demo.
- Public Earth Search STAC discovery and Sentinel-2 COG loading with provenance retained.
- Water masking, transparent quality proxies, activity-risk scoring, and plain-language explanations.

## Quickstart

Python 3.11 or newer is recommended:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/make_sample_scene.py --output data/sample_scene.tif
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is at `/docs`. Run the deterministic offline demo with `python scripts/demo.py`.

## API flow

```text
POST /ingest -> in-memory scene registry
POST /analyze -> water mask -> quality metrics -> activity risk -> explanation
GET  /risk/{water_body_id} -> latest analysis for that water body
```

`/ingest` accepts exactly one of an inline `scene`, a local `scene_path`, or a public `stac_item_url`; external fetch failures are reported rather than replaced with fabricated data.

## BRAIN: spectral and rainfall fusion

`app/spectral_features.py` computes deterministic NDWI, NDVI, NDCI, and an FAI proxy from B03/B04/B05/B08. `app/rainfall.py` summarizes caller-supplied millimetres only; empty rainfall input is explicitly marked `spectral_only`. The analysis pipeline exposes the fused, calibration-ready values under `scene_metadata.environmental_fusion` while keeping existing API fields and call signatures compatible.

## Data and scientific boundaries

The checked-in clinic and community files are synthetic/demo records and contain no patient identifiers. Clouds, atmospheric correction, adjacency effects, sensor differences, shallow bottoms, mixed pixels, and local ecology can bias the proxies. NDCI and chlorophyll-a estimates require local calibration. Human and community review remains part of the operating model.

## Development

```bash
python -m compileall app scripts config.py vendor
pytest -q
ruff check .
```

## Attribution and license

Project code is MIT-licensed under `LICENSE`. External component-level provenance and usage boundaries are documented in `vendor/README.md`. The borehole extract retains its CC BY 4.0 attribution in `data/README.md`.
