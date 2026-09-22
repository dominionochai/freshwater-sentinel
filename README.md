# Freshwater Sentinel

Freshwater Sentinel is a backend-first prototype for transparent freshwater screening. It combines water-only multispectral proxies with synthetic, privacy-preserving community and clinic-demo records. The health linkage is an exploratory screening aid: it does not establish disease transmission, diagnose patients, or replace field and laboratory confirmation.

## What is included

- FastAPI service in `app/main.py` with `/ingest`, `/analyze`, `/risk/{water_body_id}`, `/health`, `/community-profiles`, and the synthetic `/health-linkage` endpoint.
- Pydantic request and response models in `app/models.py`, including the clinic-report and linkage schemas.
- Deterministic scene generator at `scripts/make_sample_scene.py` and runnable demo at `scripts/demo.py`.
- Water masking in `app/water_masking.py`, water-quality proxies in `app/water_quality.py`, HAB/activity risk in `app/hab_risk.py`, and plain-language explanations in `app/explain.py`.
- Synthetic health linkage seed at `data/clinic_reports.json`, joined to the checked-in community profiles at `data/community_profiles.json` by `app/health_linkage.py`.
- A filtered borehole seed at `data/malawi_boreholes.csv`; provenance and licensing notes are in `data/README.md`.

## Quickstart

Python 3.11+ is recommended.

```bash
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python scripts/make_sample_scene.py --output data/sample_scene.tif
uvicorn app.main:app --reload
```

In another terminal, run the offline demo:

```bash
python scripts/demo.py
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is at `/docs`. The demo linkage can be viewed with:

```bash
curl http://127.0.0.1:8000/health-linkage
```

The response contains each synthetic report's disease, date, case count, water-point reference, matched community profile, a simple screening risk, and plain wording such as `5 cholera cases trace to this water point in Khaoleya.` Every record is marked `synthetic_demo` in `data/clinic_reports.json`.

## API flow

```text
POST /ingest -> in-memory scene registry
                 |
                 v
             POST /analyze -> water mask -> quality -> activity risk -> explanation
                 |
                 v
             GET /risk/{water_body_id}

GET /health-linkage -> data/clinic_reports.json
                        + data/community_profiles.json
                        -> water-point case totals and profile joins
```

`/health-linkage` intentionally reads checked-in demo data and returns no patient identifiers. It is not a causal inference endpoint; the word “trace” describes the synthetic water-point reference in a report.

## Data and current paths

- `data/clinic_reports.json`: synthetic cholera and typhoid reports with dates and water-point references. Do not treat these as surveillance data.
- `data/community_profiles.json`: small privacy-preserving demo profiles used for localized wording.
- `data/malawi_boreholes.csv`: filtered borehole seed; see `data/README.md` for source and license.
- `scripts/make_sample_scene.py`: deterministic GeoTIFF generator for offline development.
- `scripts/demo.py`: local end-to-end demo.
- `app/main.py`: FastAPI application and routes.
- `app/health_linkage.py`: validated report loader and report/profile/risk join.
- `tests/test_api_health_linkage.py`: minimal endpoint contract test.

## Responsible AI and scientific boundaries

This is a screening aid, not a laboratory result, regulatory decision, medical diagnosis, or safety guarantee. Clouds, atmospheric correction, adjacency effects, sensor differences, shallow bottoms, and mixed pixels can bias proxies. NDCI and chlorophyll-a estimates require local calibration; field and laboratory validation should precede public alerts. Human and community review remains part of the operating model.

## Attribution and licenses

The project code is MIT-licensed under `LICENSE`. The following external projects, datasets, concepts, and algorithms are acknowledged with their scope and license:

- **get-pak — MIT.** The compact implementation in `vendor/get-pak/methods.py` is an original local implementation of the published red/NIR turbidity and green/red-edge chlorophyll-a estimator concepts. Algorithmic inspiration is attributed to [SNO-HYBAM/get-pak](https://github.com/SNO-HYBAM/get-pak). No upstream file is copied into this repository.
- **OmniWaterMask — MIT.** `app/water_masking.py` exposes an optional external OmniWaterMask integration point; the default remains the local MNDWI/NDVI mask. No OmniWaterMask source is copied here. Any deployment using the external package must retain its MIT license and attribution.
- **boreholelabdata — CC BY 4.0.** `data/malawi_boreholes.csv` is a filtered extract of [openwashdata/boreholelabdata](https://github.com/openwashdata/boreholelabdata), licensed under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). The extract retains only fields needed by this prototype.
- **One-Health-Database-Africa — MIT.** The cross-domain health/water linkage concept is attributed to [ecohealthalliance/One-Health-Database-Africa](https://github.com/ecohealthalliance/One-Health-Database-Africa), whose concept and code are MIT-licensed. This repository copies none of its data; `data/clinic_reports.json` is synthetic/demo data created for this project.
- **Water-quality algorithms.** `app/water_quality.py` implements the NDCI formula `(B05 - B04) / (B05 + B04)` and a transparent chlorophyll-a screening proxy derived from Mishra & Mishra (2012), *Normalized difference chlorophyll index: A novel model for remote estimation of chlorophyll-a concentration in turbid productive waters*. The Python implementation is original, is not a copy of source code, and is a screening proxy requiring local calibration and validation.

See `vendor/README.md` for the same component-level provenance and usage boundaries.

## Development

```bash
python -m compileall app scripts config.py vendor
pytest -q
```

The sample scene is deterministic (`numpy` seed 7), so offline smoke tests and demos are reproducible.
