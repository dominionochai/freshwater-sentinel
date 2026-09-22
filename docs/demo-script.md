# Fresh Water Sentinel — Demo Script (4:15)

## Elevator Pitch (60s)
Fresh Water Sentinel is a One Health early-warning system for drinking water in Malawi. We model every water point as a node in a living network — boreholes, lab tests, dependent communities, satellite signals. When one borehole turns anomalous, FWS doesn't just flag it: it traces who depends on that water, who shares its risk signature, and where exposure will spread next. It then tells the response team ONE place to act, with VERIFIED-SAFE alternatives, and if lab evidence is too thin, it fails closed: FIELD SAMPLE REQUIRED. After the response, FWS grades itself — hit, miss, lead time — and feeds that outcome back into the risk engine. Detect early. Verify before acting. Fail safely. Learn from every outcome.

## The 10 Modules
1. EYES — sees water color, turbidity, bloom signals from fresh Sentinel-2 tiles over Malawi
2. MEMORY — knows the real infrastructure: WPdx water points + OpenWashData lab tests (Khaoleya borehole 4: turbidity 0.1 NTU, faecal coliforms)
3. BRAIN — fuses satellite + WHO cholera history + rainfall into a district risk score that RISES BEFORE cases; says FIELD SAMPLE REQUIRED when evidence is thin
4. SENTINEL — catches previously unseen anomalies, not just known patterns
5. NETWORK — borehole A anomalous -> who depends on it, what shares its signature, where risk propagates -> VERIFIED SAFE alternatives ranked
6. DECISION — one clear act here, not 50 red dots
7. VOICE — SMS + prerecorded Chichewa voice line, Chipatala Cha Pa Foni pattern
8. HANDS — turns the warning into field response: reroute, close the point, sample the suspect
9. VERIFY — grades itself after the alert: HIT, MISS, lead time in weeks
10. MEMORY 2.0 — feeds outcomes back into risk scoring. self-correcting loop

## Demo Script (4:15)
0:00-0:30 HOOK — open on the Malawi mission dashboard. Narration: a community shares one borehole. one bad source, many sick people. FWS was built to break that chain.
0:30-1:15 EYES + MEMORY + BRAIN — click satellite panel: fresh Sentinel-2 scene, false color, water mask. Show registry: Khaoleya borehole 4, lab values. Show risk map: one district RISING, before any cases. The forecast leads, it doesn't lag.
1:15-2:00 SENTINEL + NETWORK — DEMO RUN: anomaly appears at one borehole (red). affected settlements light amber. verified-safe alternatives turn green with distance + evidence. One bad node, a whole subgraph at risk — and we already know the safe way out.
2:00-2:30 DECISION + SAFETY — the system shows ONE act here. Then lab evidence expires: FIELD SAMPLE REQUIRED banner. No current lab proof = no unsafe action. Ever.
2:30-3:15 VOICE + HANDS — VOICE panel: SMS preview in English + Swahili, plus the Chichewa call-in script (Chipatala Cha Pa Foni pattern). HANDS panel: field task queue — verify source, sample suspect, confirm alternative — statuses flip pending -> in-progress -> done.
3:15-3:45 VERIFY + MEMORY 2.0 — timeline: alert -> action -> following weeks. HIT, lead time 3 weeks. The system just taught itself what worked.
3:45-4:15 IMPACT + CLOSE — OneAquaHealth live strip (real public API data: T5, C16, C17 macroinvertebrates + nitrate) + architecture. Close: detect early, verify before acting, fail safely. Fresh Water Sentinel.
