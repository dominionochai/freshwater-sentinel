# Vendor provenance

This directory contains original code and retained license text; no upstream source files were fetched or copied.

- [`vendor/get-pak/methods.py`](get-pak/methods.py) is an original compact implementation of the published red/NIR turbidity and green/red-edge chlorophyll-a screening estimators, with algorithmic inspiration attributed to [get-pak](https://github.com/SNO-HYBAM/get-pak) (MIT).
- [`vendor/get-pak/LICENSE`](get-pak/LICENSE) is the get-pak MIT license text already available in this repository's local history.
- [`app/water_masking.py`](../app/water_masking.py) is an original MNDWI/NDVI implementation inspired by and attributed to [WaterDetect](https://github.com/cordmaur/WaterDetect). No WaterDetect code is vendored here.
- OmniWaterMask is an optional, default-off integration point. It is not required to run this project and no OmniWaterMask source is copied here; deployments using an external OmniWaterMask implementation must retain its MIT license and attribution.
- [`app/water_quality.py`](../app/water_quality.py) implements the NDCI formula `(B05 - B04) / (B05 + B04)` and a transparent quadratic chlorophyll-a screening proxy derived from Mishra & Mishra (2012), *Normalized difference chlorophyll index: A novel model for remote estimation of chlorophyll-a concentration in turbid productive waters*. The implementation is original Python and is not a copy of source code.

## Usage

The default application path remains MNDWI/NDVI:

```python
from app.water_masking import create_water_mask
from app.water_quality import calculate_ndci, detect_chlorophyll_a_threshold

mask, diagnostics = create_water_mask(bands)
ndci = calculate_ndci(bands["B04"][mask], bands["B05"][mask])
alert = detect_chlorophyll_a_threshold(chlorophyll_a_estimates)
```

To opt into an installed OmniWaterMask adapter, pass `use_omniwatermask=True`. Missing or failing optional implementations automatically fall back to MNDWI/NDVI. NDCI and chlorophyll-a values are screening proxies: atmospheric correction, local field calibration, cloud/shadow masking, and laboratory validation are required before operational or regulatory use.
