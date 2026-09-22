# Frontend wiring specification

## Scope and source of truth

This contract is based **only** on these exact files at commit `63ed9e08a6dc06d406ee0dae3b2c7fb934a6c1d1`:

- `app/network_routes.py`
- `app/models.py`
- `app/network_models.py`
- `app/main.py`

It does not require decoding or inspecting `frontend/index.html`. The FastAPI app is defined in `app/main.py`; the network router has prefix `/network`.

## Routes

### `GET /health`

Returns `HealthResponse`:

```json
{"status":"ok","scenes_loaded":0,"results_available":0,"version":"..."}
```

The implementation sets `status` to `"ok"`, counts the in-memory `SCENES` and `LATEST_BY_WATER_BODY` stores, and returns the application version.

### `GET /community-profiles`

Returns `list[dict[str, object]]` from `load_community_profiles()`.

**Caveat:** this route has no response model, and the four permitted files do not define the item shape. Render returned keys defensively; do not assume undocumented fields.

### `GET /health-linkage`

Returns `HealthLinkageResponse` from `build_health_linkage()`:

```json
{"synthetic":true,"source_note":"...","total_reports":0,"total_cases":0,"linkages":[]}
```

### `POST /ingest` (success status 201)

Request: `IngestRequest`; response: `IngestResponse`. Exactly one of `scene`, `scene_path`, or `stac_item_url` must be provided. The route chooses, in that order, `scene_from_payload`, `scene_from_geotiff`, or `scene_from_stac_item_url`; it creates an in-memory ID `scene_<uuid4 hex>`.

Request example:

```json
{
  "water_body_id":"demo-lake",
  "scene":{
    "acquisition_date":"2026-09-22",
    "bands":{"red":[[0.12,0.13]],"nir":[[0.21,0.22]]},
    "metadata":{"source":"inline-demo"}
  }
}
```

Response shape:

```json
{"scene_id":"scene_<uuid4 hex>","water_body_id":"demo-lake","source":"...","acquisition_date":"2026-09-22","metadata":{}}
```

`source`, date, and metadata are taken from the constructed scene; their concrete values depend on the selected ingestion source.

### `POST /analyze`

Request: `AnalyzeRequest`; response: `AnalyzeResponse`. The route looks up `scene_id` in `SCENES`; if absent it returns HTTP 404 with detail `scene not found: <scene_id>`. It calls `analyze(scene, hab_observations)`, optionally creates `human_alert` when `community_profile` is supplied, caches the result by water body, and returns it. Analysis `ValueError` becomes HTTP 422 with its string detail.

Request example:

```json
{
  "scene_id":"scene_0123456789abcdef",
  "hab_observations":[{"source":"field-team","observed_on":"2026-09-22","severity":0.7,"note":"visible bloom"}],
  "community_profile":{"community":"the community","language":"en","preferred_channel":"dashboard"}
}
```

Response key set (values below are illustrative):

```json
{
  "scene_id":"scene_0123456789abcdef",
  "water_body_id":"demo-lake",
  "acquisition_date":"2026-09-22",
  "risk":{"activity":{"score":0.7,"label":"yellow","rationale":"..."}},
  "quality":{"pixels_analyzed":2,"water_coverage":1.0,"turbidity_ntu":0.0,"chlorophyll_a_ug_l":0.0,"turbidity_p90_ntu":0.0,"chlorophyll_a_p90_ug_l":0.0,"quality_uncertainty":0.0,"ndci_mean":0.0,"ndci_chlorophyll_a_ug_l":0.0,"chlorophyll_a_threshold_exceeded":false},
  "explanation":{"summary":"...","pixels_analyzed":2,"band_signals":[],"alert_date":"2026-09-22","uncertainty":0.0,"limitations":[]},
  "water_mask":{},"scene_metadata":{},"network_analysis":null,"human_alert":null
}
```

`risk` and `water_mask` are dictionaries; their inner keys are not constrained here. `network_analysis` and `human_alert` are optional and may be `null`.

### `POST /alerts/human`

Request: `HumanAlertRequest`; response: `HumanAlert`.

```json
{"risk":{},"community_profile":null}
```

Response keys are exactly `severity`, `language`, `title`, `message`, and `action`. `risk` is `dict[str, Any]`; these files do not provide a narrower request schema.

### `GET /risk/{water_body_id}`

Returns the cached `AnalyzeResponse`. If absent, HTTP 404 detail is `no analysis found for water body: <water_body_id>`.

### `POST /network/build`

Full path comes from the router prefix plus `@router.post('/build')`. Request: `NetworkBuildRequest`. If `records` is non-empty, those records are used; otherwise `_rows()` calls `load_default_records(Path.cwd())`. Missing default records produce HTTP 422 detail `network records are required; optional fixture unavailable: <error>`. The result is stored in `NETWORKS` and returned as `n.to_dict()`.

**Caveat — plain dict response:** there is no FastAPI response model. `WaterNetwork.to_dict()` produces exactly `network_id`, `nodes`, `edges`, and `provenance`.

Request example:

```json
{"records":[],"max_distance_km":10.0,"source":"inline"}
```

Response shape example (keys only from `to_dict()`):

```json
{
  "network_id":"network-1",
  "nodes":[{"node_id":"node-1","name":"Upstream","latitude":0.0,"longitude":0.0,"source":"inline","safety_state":"FIELD SAMPLE REQUIRED","community":null,"metadata":{}}],
  "edges":[{"upstream":"node-1","downstream":"node-2","distance_km":1.0,"relation":"proximity"}],
  "provenance":[]
}
```

### `POST /network/analyze`

Full path comes from the router prefix plus `@router.post('/analyze')`. Request: `NetworkAnalyzeRequest`. If a supplied `network_id` is present in `NETWORKS`, it is used. Otherwise the route builds from `records` (or default records when empty), stores the network, analyzes it, and returns `analysis.to_dict()`.

**Caveat — plain dict response:** there is no FastAPI response model. `NetworkAnalysis.to_dict()` produces exactly `network_id`, `alert_node_ids`, `propagation`, `alternatives`, `uncertainty_state`, and `dashboard`.

Request example:

```json
{"network_id":"network-1","records":[],"alert_node_ids":["node-1"],"max_distance_km":10.0,"max_hops":3,"decay":0.75,"alternatives_limit":5}
```

Response shape example:

```json
{
  "network_id":"network-1",
  "alert_node_ids":["node-1"],
  "propagation":[{"node_id":"node-2","source_node_id":"node-1","hops":1,"risk_score":0.56,"state":"UNSAFE","uncertainty_state":"FIELD SAMPLE REQUIRED","rationale":"..."}],
  "alternatives":[{"node_id":"node-3","name":"Downstream point","distance_km":2.0,"safety_state":"SAFE","rationale":"..."}],
  "uncertainty_state":"FIELD SAMPLE REQUIRED",
  "dashboard":{}
}
```

`dashboard` is `dict[str, Any]`; its inner keys are not defined in the permitted files and must not be invented.

## Exact Pydantic fields, types, defaults, and constraints

A field without a default below is required. `Field` constraints are part of the implemented contract.

### `app.models`

- `ScenePayload`: `acquisition_date: date | None = None`; `bands: dict[str, list[list[float]]]` required, `min_length=1`; `metadata: dict[str, Any] = Field(default_factory=dict)`.
- `IngestRequest`: `water_body_id: str` required, `min_length=1`, `max_length=120`, pattern `^[A-Za-z0-9_.\-/]+$`; `scene: ScenePayload | None = None`; `scene_path: str | None = None`; `stac_item_url: str | None = None`; `acquisition_date: date | None = None`.
- `IngestResponse`: `scene_id: str`; `water_body_id: str`; `source: str`; `acquisition_date: date`; `metadata: dict[str, Any] = Field(default_factory=dict)`.
- `HABObservation`: `source: str` required, min 1/max 120; `observed_on: date`; `severity: float` with `ge=0.0, le=1.0`; `note: str | None = Field(default=None, max_length=500)`.
- `CommunityProfile`: `names: list[str] = Field(default_factory=list)`; `community: str = Field(default="the community", min_length=1, max_length=120)`; `children: list[Any] = Field(default_factory=list)`; `school: Any | None = None`; `pets: list[Any] = Field(default_factory=list)`; `name: str = Field(default="the community", min_length=1, max_length=120)`; `language: Literal["en", "sw"] = "en"`; `preferred_channel: Literal["dashboard", "sms", "whatsapp"] = "dashboard"`.
- `HumanAlert`: `severity: Literal["green", "yellow", "red"]`; `language: Literal["en", "sw"]`; `title: str`; `message: str`; `action: str`.
- `HumanAlertRequest`: `risk: dict[str, Any]`; `community_profile: CommunityProfile | None = None`.
- `AnalyzeRequest`: `scene_id: str` required, min length 1; `hab_observations: list[HABObservation] = Field(default_factory=list, max_length=50)`; `community_profile: CommunityProfile | None = None`.
- `ActivityRisk`: `score: float` with `ge=0.0, le=1.0`; `label: str`; `rationale: str`.
- `QualitySummary`: required `pixels_analyzed: int`, `water_coverage: float`, `turbidity_ntu: float`, `chlorophyll_a_ug_l: float`, `turbidity_p90_ntu: float`, `chlorophyll_a_p90_ug_l: float`, `quality_uncertainty: float`; `ndci_mean: float = 0.0`; `ndci_chlorophyll_a_ug_l: float = 0.0`; `chlorophyll_a_threshold_exceeded: bool = False`.
- `Explanation`: required `summary: str`, `pixels_analyzed: int`, `band_signals: list[str]`, `alert_date: date`, `uncertainty: float`, `limitations: list[str]`.
- `AnalyzeResponse`: required `scene_id: str`, `water_body_id: str`, `acquisition_date: date`, `risk: dict[str, ActivityRisk]`, `quality: QualitySummary`, `explanation: Explanation`, `water_mask: dict[str, Any]`; `scene_metadata: dict[str, Any] = Field(default_factory=dict)`; `network_analysis: dict[str, Any] | None = None`; `human_alert: HumanAlert | None = None`.
- `HealthResponse`: `status: str`; `scenes_loaded: int`; `results_available: int`; `version: str` (all required).
- `HealthReport`: `report_id: str` required min 1/max 120; `disease: Literal["cholera", "typhoid"]`; `report_date: date`; `case_count: int` with `ge=0`; `water_point_id: str` required min 1/max 120; `community: str` required min 1/max 120; `source: Literal["synthetic_demo"] = "synthetic_demo"`.
- `HealthRisk`: `score: float` with `ge=0.0, le=1.0`; `label: Literal["green", "yellow", "red"]`; `rationale: str`.
- `HealthLinkage`: `report_id: str`; `disease: Literal["cholera", "typhoid"]`; `report_date: date`; `cases: int`; `water_point_id: str`; `community: str`; `community_profile: CommunityProfile | None = None`; `risk: HealthRisk`; `plain_language: str`.
- `HealthLinkageResponse`: `synthetic: bool = True`; `source_note: str`; `total_reports: int`; `total_cases: int`; `linkages: list[HealthLinkage]`.

Additional implemented validation: `ScenePayload` requires all band arrays to be non-empty rectangular arrays with one common shape. `IngestRequest` requires exactly one of `scene`, `scene_path`, or `stac_item_url`. Models configure extra fields as `forbid` where declared (`ScenePayload`, `IngestRequest`, `AnalyzeRequest`, `HumanAlertRequest`, `HealthReport`), and `ignore` where declared for the network request models below.

### `app.network_models`

`SafetyState = Literal["SAFE", "UNSAFE", "FIELD SAMPLE REQUIRED"]`; `SAFE = "SAFE"`.

- `NetworkNode` frozen dataclass: `node_id: str`; `name: str`; `latitude: float`; `longitude: float`; `source: str`; `safety_state: str = "FIELD SAMPLE REQUIRED"`; `community: str | None = None`; `metadata: dict[str, Any] = field(default_factory=dict)`.
- `NetworkEdge` frozen dataclass: `upstream: str`; `downstream: str`; `distance_km: float`; `relation: str = "proximity"`.
- `WaterNetwork` frozen dataclass: `network_id: str`; `nodes: tuple[NetworkNode, ...]`; `edges: tuple[NetworkEdge, ...]`; `provenance: tuple[dict[str, Any], ...] = ()`.
- `PropagationEvent` frozen dataclass: `node_id: str`; `source_node_id: str | None`; `hops: int`; `risk_score: float`; `state: str`; `uncertainty_state: str`; `rationale: str`.
- `AlternativeWaterPoint` frozen dataclass: `node_id: str`; `name: str`; `distance_km: float | None`; `safety_state: str`; `rationale: str`.
- `NetworkAnalysis` frozen dataclass: `network_id: str`; `alert_node_ids: tuple[str, ...]`; `propagation: tuple[PropagationEvent, ...]`; `alternatives: tuple[AlternativeWaterPoint, ...]`; `uncertainty_state: str`; `dashboard: dict[str, Any]`.
- `NetworkBuildRequest`: `records: list[dict[str, Any]] = Field(default_factory=list)`; `max_distance_km: float = Field(10, gt=0, le=500)`; `source: str = "inline"`; Pydantic `extra="ignore"`.
- `NetworkAnalyzeRequest`: `network_id: str | None = None`; `records: list[dict[str, Any]] = Field(default_factory=list)`; `alert_node_ids: list[str] = Field(default_factory=list)`; `max_distance_km: float = Field(10, gt=0, le=500)`; `max_hops: int = Field(3, ge=0, le=20)`; `decay: float = Field(0.75, gt=0, le=1)`; `alternatives_limit: int = Field(5, ge=0, le=100)`; Pydantic `extra="ignore"`.

`WaterNetwork.to_dict()` returns exactly `network_id`, `nodes` (list of `asdict` nodes), `edges` (list of `asdict` edges), and `provenance` (list). `NetworkAnalysis.to_dict()` returns exactly `network_id`, `alert_node_ids` (list), `propagation` (list of `asdict` events), `alternatives` (list of `asdict` alternatives), `uncertainty_state`, and `dashboard`.

## Provenance and UI states

Expose provenance rather than presenting derived data as ground truth:

- Ingest: `source`, `acquisition_date`, `metadata`; analysis: `scene_metadata`.
- Network node: `source`, `safety_state`, optional `community`, `metadata`; build: `provenance`.
- Network analysis: `uncertainty_state`; propagation also has `uncertainty_state`; alternatives have `safety_state`.
- Health linkage: `synthetic`, `source_note`; each linkage has `risk` and `plain_language`. `HealthReport.source` is fixed to `synthetic_demo`.
- Preserve exact safety labels `SAFE`, `UNSAFE`, and `FIELD SAMPLE REQUIRED`. Treat `FIELD SAMPLE REQUIRED` as uncertainty, never as a safe result.

Add a new **Network Alert** panel and a clearly labeled **DEMO** button without deleting or replacing existing UI. The panel must support: idle; loading; ready; explicit empty `propagation`/`alternatives`; provenance-visible; validation error (HTTP 422); not found (HTTP 404); and network/API failure with retry. On failure preserve the existing UI and last valid panel state, mark the network panel unavailable, and show the returned HTTP detail when present. Do not fabricate fallback fields. The DEMO button may call the documented endpoints, but must not require `frontend/index.html` decoding and must not modify application code or `data/manifest.json` for this documentation task.
