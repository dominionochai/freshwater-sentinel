# Feature Status

| Module | Contract | Status | Evidence |
|---|---|---|---|
| EYES | EYES — Sentinel-2 pulls fresh Malawi tiles; sees water color, turbidity, bloom signals. | Partial | Earth Search Sentinel-2 code; no Malawi-specific/live evidence. |
| MEMORY | MEMORY — real registry: WPdx water points + OpenWashData lab tests (Khaoleya borehole 4, measured turbidity + faecal coliforms). | Partial | Local boreholes/community data; no verified WPdx/OpenWashData/Khaoleya-4 record. |
| BRAIN | BRAIN — forecast engine: satellite signal + WHO cholera history + rainfall → risk score per district, RISES before cases, says 'FIELD SAMPLE REQUIRED' when evidence is thin. | Partial | Spectral + rainfall and synthetic health linkage; no WHO/district forecast. |
| SENTINEL | SENTINEL — detects previously unseen anomalies, not just known patterns. | Todo | No dedicated unseen-anomaly detector. |
| NETWORK | NETWORK — models water as a graph: borehole A anomalous → who depends on it, what shares its signature, where exposure propagates → VERIFIED SAFE alternatives ranked. | Built | Graph/propagation/alternatives and FIELD SAMPLE REQUIRED. |
| DECISION | DECISION — determine where investigation/intervention should happen first. | Partial | Prioritization logic but no independent operational validation. |
| VOICE | VOICE — push the warning through an actual local communication channel. | Partial | Local JSON outbox; no actual local channel. |
| HANDS | HANDS — turn the warning into a field response. | Partial | Field task creation/rerouting. |
| VERIFY | VERIFY — measure whether the intervention actually worked. | Partial | Alert grading, not intervention-effect measurement. |
| MEMORY 2.0 | MEMORY 2.0 — feed that new evidence back into the system. | Partial | Local alert/feedback persistence. |
| AQUA HEALTH | AQUA HEALTH — live OneAquaHealth ecosystem integration (verified unauthenticated endpoints GET https://api.enora-oah.eu/api/dashboards/city and /api/annotations/{pharmaceuticals,biotic,abiotic}). | Partial | Module exists; live unauthenticated endpoint verification incomplete. |
