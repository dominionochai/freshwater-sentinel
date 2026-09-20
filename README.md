# Urban Freshwater Sentinel

Backend-first prototype for the **OneAquaHealth IEEE Global Hackathon** (deadline: **2026-09-30**). Urban Freshwater Sentinel turns multispectral imagery into transparent freshwater bloom-risk signals that connect ecosystem health, human health, and responsible AI.

> **One Health pitch:** help communities act before a harmful algal bloom affects swimming, fishing, pets, or the wider freshwater ecosystem. The system only scores pixels classified as water, exposes the bands and uncertainty behind each signal, and keeps human decision-makers in the loop.

## What is included

- FastAPI service with `/ingest`, `/analyze`, `/health`, and `/risk/{water_body_id}`.
- Sentinel-2-style bands or a local multiband GeoTIFF input.
- MNDWI/NDVI water masking so land and vegetation do not contaminate water-quality statistics.
- Original, documented turbidity and chlorophyll-a proxy calculations inspired by public remote-sensing practice (not copied from get-pak).
- Configurable green/yellow/red risk for swimming, fishing, and pets.
- Plain-language explanations covering pixels, bands/signals, alert date, limitations, and uncertainty.
- Deterministic synthetic GeoTIFF generation for an offline demo.

## ASCII architecture

```text
Sentinel-2 scene / GeoTIFF / JSON bands
                 |
                 v
       POST /ingest  ---> scene registry
                 |
                 v
       POST /analyze (optional HAB observations)
                 |
                 +--> water_masking.py  -- water-only pixels
                 |          |
                 +--> water_quality.py  -- turbidity + chlorophyll-a proxies
                 |          |
                 +--> hab_risk.py       -- activity risk + thresholds
                 |          |
                 +--> explain.py        -- human-readable evidence/uncertainty
                 v
 GET /risk/{water_body_id}  ---> API-ready result for people and partners
```

## Quickstart

### 1. Run locally

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python scripts/make_sample_scene.py --output data/sample_scene.tif
uvicorn app.main:app --reload
```

In another terminal:

```bash
curl -X POST http://127.0.0.1:8000/ingest \\
  -H 'Content-Type: application/json' \\
  -d '{"water_body_id":"demo-lagoon","scene_path":"data/sample_scene.tif","acquisition_date":"2026-09-20"}'

# Use the returned scene_id
curl -X POST http://127.0.0.1:8000/analyze \\
  -H 'Content-Type: application/json' \\
  -d '{"scene_id":"<scene_id>"}'

curl http://127.0.0.1:8000/risk/demo-lagoon
curl http://127.0.0.1:8000/health
```

You can also send inline arrays through `scene.bands` (keys `B02`, `B03`, `B04`, `B08`, `B11`; `B12` is optional) instead of `scene_path`.

### 2. Docker

```bash
docker build -t freshwater-sentinel .
docker run --rm -p 8000:8000 freshwater-sentinel
```

The API docs are available at `http://127.0.0.1:8000/docs`.

## API behavior

- `/ingest` accepts one inline Sentinel-2-like scene or a local GeoTIFF path and returns a generated `scene_id`.
- `/analyze` runs the full deterministic pipeline. `hab_observations` can contain optional field observations with severity 0-1.
- `/risk/{water_body_id}` returns the latest analysis, including per-activity label and score, quality metrics, water-pixel count, evidence, and uncertainty.
- `/health` reports service status and number of in-memory scenes/results. This scaffold deliberately uses an in-memory registry; production deployment should add object storage and a durable metadata store.

## Responsible-AI and scientific boundaries

This is a screening aid, not a laboratory result, regulatory decision, or medical/safety guarantee. Cloud, atmospheric correction, adjacency effects, sensor differences, shallow bottoms, and mixed pixels can bias proxies. Thresholds are explicit in `config.py`, uncertainty is surfaced, and field/laboratory validation should precede public alerts. Human and community review remains part of the operating model.

## Development

```bash
python -m compileall app scripts
pytest -q
```

The sample scene is deterministic (`numpy` seed 7), so offline smoke tests and demos are reproducible.

## License

MIT
