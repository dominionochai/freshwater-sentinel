# Vendor provenance and attribution

This directory contains small local adapters and retained license text. It does not contain copied upstream source for optional integrations. Keep the attribution and license notices below with distributions of this repository.

## Component attribution

- **get-pak — MIT.** `vendor/get-pak/methods.py` is an original compact local implementation of the published red/NIR turbidity and green/red-edge chlorophyll-a estimator concepts. The algorithmic inspiration is attributed to [SNO-HYBAM/get-pak](https://github.com/SNO-HYBAM/get-pak). The retained license text is `vendor/get-pak/LICENSE`; no upstream file was copied.
- **OmniWaterMask — MIT.** OmniWaterMask is an optional external integration point used by `app/water_masking.py`; it is disabled by default and no OmniWaterMask source is vendored here. Deployments that install or call the external implementation must retain its MIT license and attribution.
- **boreholelabdata — CC BY 4.0.** The checked-in `data/malawi_boreholes.csv` is a filtered extract of [openwashdata/boreholelabdata](https://github.com/openwashdata/boreholelabdata), licensed under [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). It is not vendor code, but its dataset provenance is recorded here because the application consumes it.
- **One-Health-Database-Africa — MIT.** The health/water linkage concept and code are attributed to [ecohealthalliance/One-Health-Database-Africa](https://github.com/ecohealthalliance/One-Health-Database-Africa), under MIT. This project does not copy that project's data. `data/clinic_reports.json` contains synthetic/demo cholera and typhoid records only.
- **Water-quality algorithms.** `app/water_quality.py` contains an original Python implementation of the NDCI formula `(B05 - B04) / (B05 + B04)` and a transparent chlorophyll-a screening proxy derived from Mishra & Mishra (2012), *Normalized difference chlorophyll index: A novel model for remote estimation of chlorophyll-a concentration in turbid productive waters*. These are screening algorithms, not validated regulatory or laboratory measurements; atmospheric correction, field calibration, and laboratory validation remain necessary.

## Usage boundaries

The default mask is the local MNDWI/NDVI implementation in `app/water_masking.py`. To opt into an installed external OmniWaterMask adapter, call `create_water_mask(..., use_omniwatermask=True)`; missing, failing, or incompatible optional integrations fall back to the local mask.

The get-pak-inspired adapter is available through `vendor/get_pak_methods.py` and the implementation in `vendor/get-pak/methods.py`. The current API and demo paths are documented in the repository root `README.md`; health-linkage code is in `app/health_linkage.py` and its synthetic input is `data/clinic_reports.json`.

All health reports are synthetic/demo records. The `/health-linkage` endpoint joins them to `data/community_profiles.json` and computes a simple water-point screening signal; it is not evidence of disease transmission or a clinical conclusion.
