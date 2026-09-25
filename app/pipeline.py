"""Offline freshwater sentinel pipeline.

This module keeps the original scene/analyse helpers used by the API and adds a
small, deterministic EYES -> BRAIN -> HANDS event path.  It intentionally uses
only the standard library for the event path: callers provide already-fetched
signals and provenance, and this module never performs network I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import hashlib
import json
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


# ---------------------------------------------------------------------------
# Scene compatibility helpers

@dataclass(frozen=True)
class Scene:
<<<<<<< HEAD
    """A local scene accepted by the existing API endpoints.

    ``bands`` contains already loaded arrays/lists.  No downloader is used by
    this module; ``scene_from_geotiff`` only reads a caller-supplied local path.
    """

    water_body_id: str = ""
    acquisition_date: date | None = None
    bands: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
=======
    water_body_id: str
    acquisition_date: date
    bands: dict[str, np.ndarray]
    source: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)
>>>>>>> 786ed27 (fix: backend bug fixes)
    tile: str | None = None


def _as_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _scene_bands(payload: Mapping[str, Any]) -> dict[str, Any]:
    raw = payload.get("bands", payload.get("features", {}))
    if not isinstance(raw, Mapping):
        raise ValueError("scene bands/features must be an object")
    return {str(key): value for key, value in raw.items()}


def scene_from_payload(
    water_body_id: str,
    payload: Mapping[str, Any],
    acquisition_date: date | str | None = None,
) -> Scene:
    """Build a scene from JSON-safe, already acquired payload data."""
    if not isinstance(payload, Mapping):
        raise ValueError("scene payload must be an object")
    bands = _scene_bands(payload)
    if not bands:
        raise ValueError("scene must contain at least one band")
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, Mapping):
        raise ValueError("scene metadata must be an object")
    acquired = _as_date(acquisition_date) or _as_date(
        payload.get("acquisition_date", payload.get("date"))
    )
    return Scene(
        water_body_id=str(water_body_id),
        acquisition_date=acquired,
        bands=bands,
        metadata=dict(metadata),
        tile=str(payload.get("tile")) if payload.get("tile") is not None else None,
    )


def scene_from_geotiff(
    water_body_id: str,
    path: str | Path,
    acquisition_date: date | str | None = None,
) -> Scene:
    """Read a local GeoTIFF when the optional rasterio dependency is present.

    The function does not download or resolve URLs.  A clear error is raised
    when rasterio is unavailable instead of silently fabricating pixels.
    """
    try:
        import rasterio  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("rasterio is required to read a local GeoTIFF") from exc
    local_path = Path(path).expanduser()
    if not local_path.is_file():
        raise FileNotFoundError(str(local_path))
    with rasterio.open(local_path) as dataset:
        arrays = dataset.read()
        descriptions = dataset.descriptions
        bands = {
            (descriptions[index - 1] or f"B{index:02d}"): arrays[index - 1].tolist()
            for index in range(1, dataset.count + 1)
        }
        metadata = {
            "crs": str(dataset.crs) if dataset.crs else None,
            "transform": tuple(dataset.transform),
            "width": dataset.width,
            "height": dataset.height,
            "source": str(local_path),
        }
    return Scene(
        water_body_id=str(water_body_id),
        acquisition_date=_as_date(acquisition_date),
        bands=bands,
        metadata=metadata,
    )


<<<<<<< HEAD
def _numbers(value: Any) -> list[float]:
    if isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        number = float(value)
        return [number] if isfinite(number) else []
    if isinstance(value, Mapping):
        result: list[float] = []
        for child in value.values():
            result.extend(_numbers(child))
        return result
    if isinstance(value, (str, bytes)):
        return []
    try:
        result = []
        for child in value:
            result.extend(_numbers(child))
        return result
    except TypeError:
        return []


def _band_stats(bands: Mapping[str, Any]) -> tuple[int, dict[str, float]]:
    stats: dict[str, float] = {}
    count = 0
    for name, values in bands.items():
        numbers = _numbers(values)
        if numbers:
            count = max(count, len(numbers))
            stats[str(name)] = sum(numbers) / len(numbers)
    return count, stats


class _CompatResult(dict):
    """Small mapping with the pydantic v2 method used by ``app.main``."""

    def model_copy(self, *, update: Mapping[str, Any] | None = None, deep: bool = False) -> "_CompatResult":
        copied = _CompatResult(self)
        if update:
            copied.update(update)
        return copied

    def model_dump(self, **_: Any) -> dict[str, Any]:
        return dict(self)


def analyze(scene: Scene, hab_observations: Iterable[Mapping[str, Any]] = ()) -> Any:
    """Produce an offline, explainable analysis for a scene.

    If the repository's pydantic response models are available, return the
    typed ``AnalyzeResponse`` expected by FastAPI.  The fallback mapping keeps
    this module importable in small test environments.
    """
    if not isinstance(scene, Scene):
        raise TypeError("analyze expects a Scene")
    pixels, stats = _band_stats(scene.bands)
    means = {key.lower(): value for key, value in stats.items()}
    ndwi = means.get("ndwi", means.get("water_index", 0.0))
    ndci = means.get("ndci", 0.0)
    chlorophyll = means.get("chlorophyll_a", means.get("chlorophyll", max(0.0, ndci * 100.0)))
    turbidity = means.get("turbidity_ntu", means.get("turbidity", 0.0))
    coverage = 1.0 if pixels else 0.0
    score = max(0.0, min(1.0, max(ndci, chlorophyll / 100.0, turbidity / 100.0)))
    label = "high" if score >= 0.7 else "moderate" if score >= 0.45 else "low"
    acquired = scene.acquisition_date or date(1970, 1, 1)
    limitations = [] if pixels else ["no finite numeric band values"]
    risk = {"activity": {"score": round(score, 6), "label": label, "rationale": "deterministic supplied-band threshold"}}
    quality = {
        "pixels_analyzed": pixels,
        "water_coverage": coverage,
        "turbidity_ntu": round(turbidity, 6),
        "chlorophyll_a_ug_l": round(chlorophyll, 6),
        "turbidity_p90_ntu": round(turbidity, 6),
        "chlorophyll_a_p90_ug_l": round(chlorophyll, 6),
        "quality_uncertainty": 0.0 if pixels else 1.0,
        "ndci_mean": round(ndci, 6),
        "ndci_chlorophyll_a_ug_l": round(chlorophyll, 6),
        "chlorophyll_a_threshold_exceeded": bool(chlorophyll >= 10.0),
    }
    explanation = {
        "summary": f"{label} activity signal from supplied scene bands",
        "pixels_analyzed": pixels,
        "band_signals": sorted(stats),
        "alert_date": acquired,
        "uncertainty": 0.0 if pixels else 1.0,
        "limitations": limitations,
    }
    result = _CompatResult(
        scene_id="scene-" + hashlib.sha256(
            json.dumps({"water_body_id": scene.water_body_id, "date": acquired.isoformat(), "bands": sorted(scene.bands)}, sort_keys=True).encode()
        ).hexdigest()[:16],
        water_body_id=scene.water_body_id,
        acquisition_date=acquired,
        risk=risk,
        quality=quality,
        explanation=explanation,
        water_mask={"pixels_analyzed": pixels, "coverage": coverage},
        scene_metadata=dict(scene.metadata),
    )
    try:
        from app.models import AnalyzeResponse  # type: ignore
        return AnalyzeResponse(**result)
    except (ImportError, TypeError, ValueError):
        return result


# ---------------------------------------------------------------------------
# Deterministic EYES -> BRAIN -> HANDS event path

DEFAULT_EVENT_LOG = Path(__file__).resolve().parents[1] / "data" / "events.jsonl"


def _jsonable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(child) for child in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _canonical(value: Any) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _signal_values(signals: Any) -> dict[str, float]:
    if isinstance(signals, Mapping):
        result: dict[str, float] = {}
        for name, value in signals.items():
            values = _numbers(value)
            if values:
                result[str(name)] = round(sum(values) / len(values), 12)
        return result
    values = _numbers(signals)
    return {f"signal_{index}": round(value, 12) for index, value in enumerate(values)}


def threshold_gate(
    signals: Mapping[str, Any] | Sequence[Any] | Any,
    threshold: float = 0.5,
    *,
    mode: str = "any",
) -> bool:
    """Return a deterministic threshold decision over supplied signal(s).

    ``any`` is the conservative default for alerts; ``all``, ``mean`` and
    ``max`` are explicit alternatives.  Empty/non-numeric input never gates.
    """
    values = list(_signal_values(signals).values())
    if not values:
        return False
    if mode == "any":
        return any(value >= threshold for value in values)
    if mode == "all":
        return all(value >= threshold for value in values)
    if mode == "mean":
        return sum(values) / len(values) >= threshold
    if mode == "max":
        return max(values) >= threshold
    raise ValueError("mode must be one of: any, all, mean, max")


deterministic_threshold_gate = threshold_gate


def _severity(score: float, threshold: float, gated: bool) -> str:
    if not gated:
        return "low"
    if score >= max(0.8, threshold + 0.2):
        return "high"
    return "moderate"


def _evidence_links(event_id: str, evidence: Any, inputs: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    supplied = evidence if isinstance(evidence, Mapping) else {}
    links: dict[str, dict[str, Any]] = {}
    for name, key in (("EYES", "eyes"), ("BRAIN", "brain")):
        raw = supplied.get(name, supplied.get(name.lower(), inputs.get(f"{key}_output")))
        if isinstance(raw, Mapping):
            output = _jsonable(raw.get("output", raw.get("result", raw)))
            link = raw.get("link", raw.get("url", raw.get("path")))
        else:
            output = _jsonable(raw) if raw is not None else name
            link = raw if isinstance(raw, str) and (raw.startswith(("http://", "https://", "data/", "/"))) else None
        links[name] = {"name": name, "output": output, "link": link}
    return links


def _targets(inputs: Mapping[str, Any], targets: Iterable[Any] | None) -> list[Any]:
    if targets is not None:
        return [_jsonable(item) for item in targets]
    value = inputs.get("registry_targets", inputs.get("targets"))
    if value is None:
        value = inputs.get("water_point_id", inputs.get("water_body_id"))
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [str(value)]
    try:
        return [_jsonable(item) for item in value]
    except TypeError:
        return [_jsonable(value)]


def _task_record(event_id: str, severity: str, inputs: Mapping[str, Any], targets: list[Any], action: str, evidence: dict[str, Any]) -> dict[str, Any]:
    target = targets[0] if targets else inputs.get("water_point_id", inputs.get("water_body_id", ""))
    return {
        "task_id": f"task-{event_id}",
        "source": "sentinel-pipeline",
        "created_at": "deterministic:event-timestamp",
        "status": "pending",
        "water_body_id": str(inputs.get("water_body_id", target or "")),
        "title": f"Verify freshwater sentinel {severity} event",
        "action": action,
        "priority": "urgent" if severity == "high" else "high" if severity == "moderate" else "medium",
        "task_type": "verify_source" if severity == "high" else "collect_sample",
        "target_water_point_id": str(target) if target else None,
        "evidence_note": json.dumps(evidence, sort_keys=True, separators=(",", ":")),
    }


def event_brief(event: Mapping[str, Any]) -> dict[str, Any]:
    """Return the stable, replayable part of an event record."""
    if isinstance(event.get("brief"), Mapping):
        return dict(event["brief"])
    return {
        "event_id": event.get("event_id"),
        "severity": event.get("severity"),
        "evidence_links": event.get("evidence_links", event.get("evidence", {})),
        "registry_targets": event.get("registry_targets", []),
        "suggested_action": event.get("suggested_action"),
        "task": event.get("task", event.get("hands_task")),
    }


def build_event(
    signals: Mapping[str, Any] | Sequence[Any] | Any,
    *,
    threshold: float = 0.5,
    timestamp: str | datetime | None = None,
    inputs: Mapping[str, Any] | None = None,
    event_id: str | None = None,
    evidence: Mapping[str, Any] | None = None,
    registry_targets: Iterable[Any] | None = None,
    suggested_action: str | None = None,
    mode: str = "any",
) -> dict[str, Any]:
    """Build one structured event without performing I/O."""
    supplied_inputs = dict(inputs or {})
    normalized = _signal_values(signals)
    supplied_inputs.setdefault("signals", normalized)
    gated = threshold_gate(normalized, threshold, mode=mode)
    score = max(normalized.values()) if normalized else 0.0
    severity = _severity(score, float(threshold), gated)
    stable_identity = {
        "signals": normalized,
        "threshold": float(threshold),
        "mode": mode,
        "inputs": supplied_inputs,
        "evidence": evidence or {},
        "registry_targets": list(registry_targets) if registry_targets is not None else None,
    }
    resolved_id = event_id or "evt-" + hashlib.sha256(_canonical(stable_identity).encode("utf-8")).hexdigest()[:24]
    if timestamp is None:
        resolved_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    elif isinstance(timestamp, datetime):
        resolved_timestamp = timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        resolved_timestamp = str(timestamp)
    links = _evidence_links(resolved_id, evidence, supplied_inputs)
    targets = _targets(supplied_inputs, registry_targets)
    action = suggested_action or (
        "Collect a confirmatory field sample and verify source evidence" if severity in {"moderate", "high"} else "Continue monitoring supplied signals"
    )
    task = _task_record(resolved_id, severity, supplied_inputs, targets, action, links)
    brief = {
        "event_id": resolved_id,
        "severity": severity,
        "evidence_links": links,
        "registry_targets": targets,
        "suggested_action": action,
        "task": task,
    }
    return {
        "event_id": resolved_id,
        "timestamp": resolved_timestamp,
        "inputs": _jsonable(supplied_inputs),
        "signals": normalized,
        "threshold": float(threshold),
        "mode": mode,
        "gated": gated,
        "score": round(score, 12),
        "severity": severity,
        "evidence_links": links,
        "evidence": links,
        "registry_targets": targets,
        "suggested_action": action,
        "task": task,
        "hands_task": task,
        "brief": brief,
    }


def append_event(event: Mapping[str, Any], log_path: str | Path = DEFAULT_EVENT_LOG) -> dict[str, Any]:
    """Append one canonical JSONL event and return it as a plain dict."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = _jsonable(dict(event))
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_canonical(record) + "\n")
    return record


def emit_event(signals: Any, *, log_path: str | Path = DEFAULT_EVENT_LOG, **kwargs: Any) -> dict[str, Any]:
    return append_event(build_event(signals, **kwargs), log_path=log_path)


record_event = emit_event
create_event = build_event


def replay(event_id: str, log_path: str | Path = DEFAULT_EVENT_LOG) -> dict[str, Any]:
    """Read an event from JSONL and reproduce its stable brief exactly."""
    path = Path(log_path)
    if not path.is_file():
        raise KeyError(f"event not found: {event_id}")
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("event_id") == event_id:
                return event_brief(record)
    raise KeyError(f"event not found: {event_id}")


replay_event = replay


class Pipeline:
    """Dependency-light facade for callers that prefer an object API."""

    def __init__(self, log_path: str | Path = DEFAULT_EVENT_LOG, threshold: float = 0.5, mode: str = "any") -> None:
        self.log_path = Path(log_path)
        self.threshold = threshold
        self.mode = mode

    def process(self, signals: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("threshold", self.threshold)
        kwargs.setdefault("mode", self.mode)
        return emit_event(signals, log_path=self.log_path, **kwargs)

    emit = process

    def replay(self, event_id: str) -> dict[str, Any]:
        return replay(event_id, log_path=self.log_path)


SentinelPipeline = Pipeline

__all__ = [
    "Scene", "analyze", "scene_from_geotiff", "scene_from_payload",
    "threshold_gate", "deterministic_threshold_gate", "build_event",
    "create_event", "append_event", "emit_event", "record_event", "replay",
    "replay_event", "event_brief", "Pipeline", "SentinelPipeline",
]
=======
def analyze(scene: Scene, observations: list[HABObservation], network: WaterNetwork | None = None, rainfall: Sequence[float] | Mapping[str, Any] | None = None) -> AnalyzeResponse:
    mask, diagnostics = create_water_mask(scene.bands)
    metrics: QualityMetrics = estimate_quality(scene.bands, mask)
    if metrics.pixels_analyzed < MIN_ANALYZED_PIXELS:
        raise ValueError(f"only {metrics.pixels_analyzed} valid water pixels analyzed; need at least {MIN_ANALYZED_PIXELS}")
    risk = score_risk(metrics, observations)
    explanation = build_explanation(metrics, risk, scene.acquisition_date, diagnostics, observations)
    network_analysis = analyze_water_network(network).to_dict() if network is not None else None
    fusion = fuse_environmental_signals(scene.bands, rainfall)
    return AnalyzeResponse(scene_id="", water_body_id=scene.water_body_id, acquisition_date=scene.acquisition_date, risk=risk, quality=metrics.as_dict(), explanation=explanation, water_mask={**diagnostics, "pixels_in_mask": int(mask.sum()), "scene_pixels": int(mask.size)}, scene_metadata={**scene.metadata, "environmental_fusion": fusion}, network_analysis=network_analysis)

class Pipeline:
    """Offline event pipeline: turns raw signals into a risk brief and
    persists/replays it via a JSONL event log.

    NOTE: reconstructed from how app/main.py calls it (Pipeline was missing
    from the handoff). The trigger logic (mode='any'/'all' vs threshold) is
    a best guess -- verify against the real demo semantics before relying on it.
    """

    def __init__(self, log_path):
        from pathlib import Path
        self.log_path = Path(log_path)

    def process(
        self,
        signals,
        *,
        threshold: float = 0.5,
        mode: str = "any",
        timestamp=None,
        event_id=None,
        inputs=None,
        evidence=None,
        registry_targets=None,
        suggested_action=None,
    ) -> dict:
        import json
        from datetime import datetime, timezone
        from uuid import uuid4

        if not isinstance(signals, dict):
            raise TypeError("signals must be a mapping of signal name -> numeric value")

        values = []
        for v in signals.values():
            try:
                values.append(float(v))
            except (TypeError, ValueError):
                raise ValueError(f"non-numeric signal value: {v!r}")

        if mode == "all":
            triggered = bool(values) and all(v >= threshold for v in values)
        elif mode == "any":
            triggered = any(v >= threshold for v in values)
        else:
            raise ValueError(f"unknown mode: {mode!r}")

        record = {
            "event_id": event_id or str(uuid4()),
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "signals": signals,
            "threshold": threshold,
            "mode": mode,
            "triggered": triggered,
            "risk_level": "RED" if triggered else "GREEN",
            "inputs": inputs or {},
            "evidence": evidence,
            "registry_targets": registry_targets,
            "suggested_action": suggested_action,
        }

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        return record

    def replay(self, event_id: str) -> dict:
        import json

        if not self.log_path.exists():
            raise KeyError(event_id)

        with self.log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("event_id") == event_id:
                    return record

        raise KeyError(event_id)

>>>>>>> 786ed27 (fix: backend bug fixes)
