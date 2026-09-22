# OneAquaHealth IEEE Global Hackathon Submission

## Recommended Track: Data-to-Insight
Fresh Water Sentinel transforms heterogeneous water-safety data into operational, explainable early-warning decisions: Malawi district-level cholera observations, water-point network relationships, field-sample status, Sentinel-2 false-color context, and live OneAquaHealth ecosystem data. It detects anomalies, propagates risk to dependent settlements, and recommends verified-safe reroutes. Safety controls ensure automation supports public-health teams without replacing laboratory confirmation.

## Project Description
Fresh Water Sentinel is a One Health early-warning system for drinking-water risks in Malawi. It models water points as an interconnected network, linking sources to dependent settlements so that an anomaly at one point can be propagated through the affected subgraph and surfaced where it may create the greatest public-health risk. The prototype combines Malawi district-level cholera data from OpenWashData (CC BY 4.0, 1,886 rows), water-network relationships, Sentinel-2 false-color context, and live OneAquaHealth ecosystem signals (verified unauthenticated endpoints: GET https://api.enora-oah.eu/api/dashboards/city and GET https://api.enora-oah.eu/api/annotations/{pharmaceuticals,biotic,abiotic}). When a water point becomes anomalous, the system identifies affected settlements, ranks potential exposure, and proposes rerouting to an alternative source only when that alternative is verified safe. If laboratory evidence is missing or stale, the system fails closed and displays FIELD SAMPLE REQUIRED rather than authorizing a potentially unsafe intervention. A VERIFY-then-act memory loop records what was detected, what was verified, what action was taken, and what outcome followed, supporting continuous improvement while preserving safety and accountability.

## Demo Video Beat Sheet
0:00-0:30 hook: a Malawi community dependent on a shared drinking-water point; one bad source affects many; FWS detects early and reroutes only when safe. 0:30-1:15 problem and network concept: Malawi map, district-level cholera context (OpenWashData, 1,886 rows, CC BY 4.0), water points become an interconnected network. 1:15-2:45 live demo: anomaly detection, affected subgraph and impacted settlements, ranked alternative water points, verified-safe reroute, FIELD SAMPLE REQUIRED fail-closed behavior, VERIFY-then-act memory loop. 2:45-3:15 OneAquaHealth live integration: GET /api/dashboards/city and annotation endpoints enriching the risk picture. 3:15-4:00 impact and architecture: ingestion, network model, anomaly detection, subgraph propagation, verification gate, rerouting, memory loop; Sentinel-2 false-color as contextual evidence, not a replacement for lab testing. 4:00-4:15 close: detect early, verify before acting, fail safely.

## Submission Checklist
- [ ] Selected track: Data-to-Insight
- [ ] Project description (above)
- [ ] 3-5 minute demo video
- [ ] Public GitHub repository: https://github.com/dominionochai/freshwater-sentinel
- [ ] Working prototype
