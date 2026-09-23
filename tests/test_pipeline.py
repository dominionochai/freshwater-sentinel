"""Small offline tests for water-only quality and API validation."""

import json

import numpy as np
import pytest

from app.models import ScenePayload
from app.pipeline import Pipeline, event_brief, threshold_gate
from app.water_masking import create_water_mask
from app.water_quality import estimate_quality


def test_water_mask_excludes_land_from_quality():
    shape = (4, 4)
    bands = {
        name: np.full(shape, 0.1, dtype=float)
        for name in ("B02", "B03", "B04", "B05", "B08", "B11")
    }
    bands["B03"][:2] = 0.20
    bands["B11"][:2] = 0.04
    bands["B08"][:2] = 0.12
    bands["B04"][:2] = 0.08
    mask, _ = create_water_mask(bands)
    assert int(mask.sum()) == 8
    metrics = estimate_quality(bands, mask)
    assert metrics.pixels_analyzed == 8


def test_scene_payload_rejects_mismatched_shapes():
    with pytest.raises(ValueError):
        ScenePayload(bands={"B02": [[0.1, 0.2]], "B03": [[0.1]]})


def _offline_inputs():
    """Replacement EYES/BRAIN outputs; no provider or network access is used."""
    return {
        "eyes_output": {
            "output": {"ndci": 0.91, "source": "mock-eyes"},
            "link": "https://evidence.example/eyes/scene-42",
        },
        "brain_output": {
            "output": {"risk": "elevated", "source": "mock-brain"},
            "link": "https://evidence.example/brain/scene-42",
        },
        "water_body_id": "WB-42",
        "registry_targets": [
            "registry://water-point/WB-42",
            "registry://program/freshwater-sentinel",
        ],
    }


def test_threshold_gate_blocks_below_and_emits_above(tmp_path):
    assert threshold_gate({"EYES": [0.49], "BRAIN": [0.20]}, 0.5) is False
    assert threshold_gate({"EYES": [0.51], "BRAIN": [0.20]}, 0.5) is True

    pipeline = Pipeline(log_path=tmp_path / "events.jsonl", threshold=0.5)
    below = pipeline.process(
        {"EYES": [0.20], "BRAIN": [0.30]},
        inputs=_offline_inputs(),
        timestamp="2026-09-23T09:00:00Z",
        event_id="evt-below",
    )
    above = pipeline.process(
        {"EYES": [0.80], "BRAIN": [0.90]},
        inputs=_offline_inputs(),
        timestamp="2026-09-23T09:01:00Z",
        event_id="evt-above",
    )

    assert below["event_id"] == "evt-below"
    assert below["gated"] is False
    assert above["event_id"] == "evt-above"
    assert above["gated"] is True
    assert above["severity"] == "high"

    records = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert [record["event_id"] for record in records] == ["evt-below", "evt-above"]


def test_emitted_event_has_evidence_targets_hands_task_and_replay(tmp_path):
    log_path = tmp_path / "events.jsonl"
    pipeline = Pipeline(log_path=log_path, threshold=0.5)
    action = "Collect a confirmatory field sample and verify source evidence"
    event = pipeline.process(
        {"EYES": [0.82], "BRAIN": [0.91]},
        inputs=_offline_inputs(),
        timestamp="2026-09-23T09:02:00Z",
        event_id="evt-replayable",
        suggested_action=action,
    )

    assert event["event_id"] == "evt-replayable"
    assert event["severity"] == "high"
    assert event["gated"] is True
    assert event["evidence_links"]["EYES"] == {
        "name": "EYES",
        "output": {"ndci": 0.91, "source": "mock-eyes"},
        "link": "https://evidence.example/eyes/scene-42",
    }
    assert event["evidence_links"]["BRAIN"]["link"] == (
        "https://evidence.example/brain/scene-42"
    )
    assert event["registry_targets"] == [
        "registry://water-point/WB-42",
        "registry://program/freshwater-sentinel",
    ]
    assert event["suggested_action"] == action

    task = event["task"]
    assert event["hands_task"] == task
    assert task["task_id"] == "task-evt-replayable"
    assert task["source"] == "sentinel-pipeline"
    assert task["status"] == "pending"
    assert task["water_body_id"] == "WB-42"
    assert task["target_water_point_id"] == "registry://water-point/WB-42"
    assert task["action"] == action
    assert task["priority"] == "urgent"
    assert task["task_type"] == "verify_source"

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    persisted = json.loads(lines[0])
    assert persisted == event
    replayed_brief = pipeline.replay("evt-replayable")
    assert replayed_brief == event["brief"]
    assert replayed_brief == event_brief(event)
