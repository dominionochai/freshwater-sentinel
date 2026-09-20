# Vendor provenance

This directory documents upstream projects used as references or license sources:

- [get-pak](https://github.com/SNO-HYBAM/get-pak) — MIT. Its LICENSE is vendored at `vendor/get-pak/LICENSE`. It contributes Sentinel-2 inland-water-quality processing plus methods for turbidity and chlorophyll-a estimation.
- [WaterDetect](https://github.com/cordmaur/WaterDetect) — repository metadata reports Apache-2.0, while its README states GPL-3.0. No WaterDetect code is vendored here. This repository instead implements an original water-masking module at `app/water_masking.py`, based on the published MNDWI/NDVI approach, with attribution in the module's docstrings.
- [tick-tick-bloom](https://github.com/drivendataorg/tick-tick-bloom) — MIT. It is referenced as methodology for cyanobacteria bloom severity framing.

Upstream source files are linked, not copied, to keep this repository clean and license-safe.
