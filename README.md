# Urban Freshwater Sentinel

Backend-first prototype for the **OneAquaHealth IEEE Global Hackathon**. Urban Freshwater Sentinel turns multispectral imagery into transparent freshwater bloom-risk signals that connect ecosystem health, human health, and responsible AI.

> **One Health pitch:** help communities act before a harmful algal bloom affects swimming, fishing, pets, or the wider freshwater ecosystem. The system only scores pixels classified as water, exposes the bands and uncertainty behind each signal, and keeps human decision-makers in the loop.

## What is included

- FastAPI service with `/ingest`, `/analyze`, `/health`, and `/risk/{water_body_id}`.
- Sentinel-2-style bands or a local multiband GeoTIFF input.
- MNDWI/NDVI water masking so land and vegetation do not contaminate water-quality statistics.
- Optional, default-off OmniWaterMask integration with automatic MNDWI/NDVI fallback.
- Transparent turbidity and chlorophyll-a proxy calculations, including Python NDCI screening and a configurable threshold flag.
- Configurable green/yellow/red risk for swimming, fishing, and pets.
- Plain-language explanations covering pixels, bands/signals, alert date, limitations, and uncertainty.
- Deterministic synthetic GeoTIFF generation for an offline demo.

## ASCII architecture

```text
Sentinel-2 scene / GeoTIFF / JSON bands
                |
                v
       POST /ingest --> scene registry
                |
                v
       POST /analyze (optional HAB observations)
                |
                +--> water_masking.py --> water-only pixels
                |                         |
                |                         +--> optional OmniWaterMask (default off)
                +--> water_quality.py --> turbidity + chlorophyll-a + NDCI
                |                         |
                |                         +--> hab_risk.py --> activity risk
                +--> explain.py --> human-readable evidence/uncertainty
                v
       GET /risk/{water_body_id} --> API-ready result
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

curl -X POST http://127.0.0.1:8000/analyze \\
  -H 'Content-Type: application/json' \\
  -d '{"scene_id":"<scene_id>"}'

curl http://127.0.0.1:8000/risk/demo-lagoon
curl http://127.0.0.1:8000/health
```

You can also send inline arrays through `scene.bands` with keys `B02`, `B03`, `B04`, `B05`, `B08`, `B11`; `B12` is optional.

### Optional OmniWaterMask

The established MNDWI/NDVI mask is used by default. To opt into an installed OmniWaterMask implementation, call the Python API with `use_omniwatermask=True`:

```python
from app.water_masking import create_water_mask
mask, diagnostics = create_water_mask(bands, use_omniwatermask=True)
```

The adapter is import-safe: if the optional package or a compatible entry point is absent, raises during prediction, or returns the wrong shape, the existing MNDWI/NDVI mask is returned. OmniWaterMask is optional and MIT-licensed; see `vendor/README.md` for provenance.

### NDCI chlorophyll screening

`app.water_quality.calculate_ndci` implements `NDCI = (B05 - B04) / (B05 + B04)`. The quality result additionally reports `ndci_mean`, `ndci_chlorophyll_a_ug_l`, and `chlorophyll_a_threshold_exceeded`. The threshold defaults to the existing chlorophyll-a red screening breakpoint and is a screening aid, not a laboratory or regulatory result.

## API behavior

- `/ingest` accepts one inline Sentinel-2-like scene or a local GeoTIFF path and returns a generated `scene_id`.
- `/analyze` runs the deterministic pipeline. `hab_observations` can contain optional observations with severity 0–1.
- `/risk/{water_body_id}` returns the latest analysis, including per-activity label and score, quality metrics, water-pixel count, evidence, and uncertainty.
- `/health` reports service status and the number of in-memory scenes/results.

## Responsible AI and scientific boundaries

This is a screening aid, not a laboratory result, regulatory decision, or medical/safety guarantee. Clouds, atmospheric correction, adjacency effects, sensor differences, shallow bottoms, and mixed pixels can bias proxies. Thresholds are explicit in `config.py`, uncertainty is surfaced, and field/laboratory validation should precede public alerts. Human and community review remains part of the operating model.

## Recipe

- Original FastAPI pipeline: ingestion, water masking, water quality, HAB risk, explanations, and API endpoints.
- `vendor/get-pak/methods.py`: original local implementation of published estimator proxies, with MIT attribution to [get-pak](https://github.com/SNO-HYBAM/get-pak).
- `app/water_masking.py`: original MNDWI/NDVI implementation inspired by and attributed to [WaterDetect](https://github.com/cordmaur/WaterDetect); no WaterDetect code is vendored.
- Optional OmniWaterMask adapter: MIT-licensed external integration point; it is not required for installation and no external code is copied into this repository.
- `app/water_quality.py`: Python NDCI and chlorophyll-a threshold screening derived from the NDCI remote-sensing algorithm described by Mishra & Mishra (2012), with coefficients documented in the function docstring and intended for transparent screening rather than regulatory use.
- `vendor/README.md`: provenance notes, licensing scope, usage, and atmospheric-correction/calibration caveats.

The scientific caveats above govern these transparent screening proxies; they are not copied upstream code or validated regulatory measurements.

## Development

```bash
python -m compileall app scripts config.py vendor
pytest -q
```

The sample scene is deterministic (`numpy` seed 7), so offline smoke tests and demos are reproducible.

## License

MIT
