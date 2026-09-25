# Freshwater Sentinel frontend

This directory contains the dependency-free, offline-first field dashboard. It preserves the existing analysis view and adds Water signal, Network alert, and Health linkage views.

## Run the demo

From the repository root:

```bash
python -m http.server 8000 --directory frontend
# open http://localhost:8000
```

No build step or third-party network request is required. `assets/analysis_output.json` remains the source-compatible analysis fixture and `assets/satellite-demo.svg` is the generated local scene image.

## Offline behavior

The frontend uses local fixtures and local assets only. No network requests are made.

## Visual contract

Palette: ink `#081a2b`, navy `#0d2b45`, paper `#f4f8f7`, teal `#16c1b7`, blue `#367ca7`, amber `#f4b942`, and coral `#f05d5e`. Safety labels retain `SAFE`, `UNSAFE`, and `FIELD SAMPLE REQUIRED`; field-sample-required is uncertainty, never a safe result.

Backend tests remain the validation command: `pytest`.
