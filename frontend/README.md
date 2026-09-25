# Freshwater Sentinel frontend

A dependency-free, offline-first hackathon demo. It uses local synthetic demo records, inline SVG artwork and the existing local stylesheet—no backend, build step, API keys, CDN, or network requests.

## Run the demo

From the repository root:

```bash
python -m http.server 8000 --directory frontend
```

Open <http://localhost:8000>. The sidebar independently opens EYES, BRAIN, NETWORK, VOICE, HANDS and VERIFY. The EYES scene switches between natural color and Sentinel-2-style false color; HANDS tasks are clickable. **START 8-BEAT DEMO** and **Next beat** remain optional presenter controls.

All readings and outcomes are synthetic. Satellite/risk signals are screening evidence; field sampling and laboratory confirmation are required. The SMS panels are mockups and do not send messages.
