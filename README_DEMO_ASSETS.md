# Offline demo asset exporter

Generate the deterministic GeoTIFF, percentile-stretched composites, water-mask
overlay, full pipeline analysis JSON, and English/Swahili community alerts with:

```bash
python scripts/export_demo_assets.py
```

The command is fully offline and uses the repository's real
`scripts/make_sample_scene.py:create_sample_scene`, `app.pipeline`,
`app.water_masking`, `app.alerts`, and `app.community_data` implementations.
It writes `data/sample_scene.tif`, `assets/rgb_composite.png`,
`assets/b08_nir_composite.png`, `assets/water_mask_overlay.png`, and
`assets/analysis.json`. The exporter is not run as part of the commit.
