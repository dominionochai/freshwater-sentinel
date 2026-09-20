# Vendor provenance

This directory contains original code and retained license text; no upstream
source files were fetched or copied.

- [`vendor/get-pak/methods.py`](get-pak/methods.py) is an original compact
  implementation of the published red/NIR turbidity and green/red-edge
  chlorophyll-a screening estimators, with algorithmic inspiration attributed
  to [get-pak](https://github.com/SNO-HYBAM/get-pak) (MIT).
- [`vendor/get-pak/LICENSE`](get-pak/LICENSE) is the get-pak MIT license text
  already available in this repository's local history; it is retained for
  provenance and is not a copy of upstream implementation code.
- [`app/water_masking.py`](../app/water_masking.py) is an original MNDWI/NDVI
  implementation inspired by and attributed to
  [WaterDetect](https://github.com/cordmaur/WaterDetect). No WaterDetect code
  is vendored here.
- WaterDetect license provenance is discrepant: repository metadata reports
  Apache-2.0 while the upstream README states GPL-3.0. This note records the
  discrepancy without asserting a resolution or relicensing this project.

The estimator coefficients are generic screening defaults. Atmospheric
correction, local field calibration, cloud/shadow masking, and laboratory
validation are required before operational or regulatory use.
