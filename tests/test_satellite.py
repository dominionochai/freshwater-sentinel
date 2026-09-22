from __future__ import annotations

import numpy as np

from app.satellite import compute_indices, fetch_preview, summarize_ndwi


def test_ndwi_and_ndvi_math_on_synthetic_arrays() -> None:
    green = np.array([[0.6, 0.2], [0.8, 0.1]])
    nir = np.array([[0.2, 0.6], [0.4, 0.1]])
    red = np.array([[0.2, 0.1], [0.2, 0.3]])
    ndwi, ndvi = compute_indices(green, nir, red)
    np.testing.assert_allclose(ndwi, [[0.5, -0.5], [1 / 3, 0.0]])
    np.testing.assert_allclose(ndvi, [[0.0, 5 / 7], [1 / 3, -0.5]])


def test_water_mask_and_summary_are_json_compatible() -> None:
    summary = summarize_ndwi(np.array([[-0.5, 0.1], [0.4, np.nan]]))
    assert summary == {"ndwi_min": -0.5, "ndwi_mean": 0.0, "ndwi_max": 0.4, "water_pixel_share": 2 / 3, "anomaly_flag": True}


def test_preview_tries_s3_then_azure_and_walks_back_after_404() -> None:
    calls: list[str] = []

    def mocked_download(url: str) -> bytes:
        calls.append(url)
        if "2026/9/S2A_MSIL2A_20260922" in url:
            raise FileNotFoundError(url)
        if "2026/9/20260921" in url and "sentinel-cogs" in url:
            raise FileNotFoundError(url)
        return b"preview"

    result = fetch_preview("36/L/VM", "2026-09-22", item_id="S2A_MSIL2A_20260922T075631_R035_T36LVM_20260922T125740", downloader=mocked_download)
    assert result["scene_date"] == "2026-09-21"
    assert result["content"] == b"preview"
    assert calls[0].startswith("https://sentinel-cogs.s3.us-west-2.amazonaws.com/")
    assert any(url.startswith("https://ai4edataeuwest.blob.core.windows.net/") for url in calls)
