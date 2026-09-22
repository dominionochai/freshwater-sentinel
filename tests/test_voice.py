import json

from app import voice as voice_module
from app.voice import (
    VoiceOutbox,
    build_voice_script,
    deliver_voice,
    dispatch_voice,
    render_alert_voice,
)


class MockVoice:
    def __init__(self):
        self.calls = []

    def synthesize(self, text):
        self.calls.append(text)
        return {"mock": True, "length": len(text)}


def test_voice_uses_injected_mock_provider(tmp_path):
    provider = MockVoice()
    result = deliver_voice("hello", provider=provider, outbox=VoiceOutbox(tmp_path / "outbox.jsonl"))
    assert result["status"] == "delivered"
    assert result["receipt"]["mock"] is True
    assert provider.calls == ["hello"]
    assert not (tmp_path / "outbox.jsonl").exists()


def test_voice_falls_back_to_outbox_on_provider_error(tmp_path):
    class Broken:
        def synthesize(self, text):
            raise TimeoutError("mock timeout")

    outbox = VoiceOutbox(tmp_path / "outbox.jsonl")
    result = deliver_voice("retry me", provider=Broken(), outbox=outbox)
    assert result["status"] == "queued"
    assert result["fallback_reason"] == "TimeoutError"
    assert [item.text for item in outbox.pending()] == ["retry me"]


def test_alert_rendering_is_short_and_explicit():
    assert render_alert_voice({"severity": "red", "title": "Lake", "action": "Verify"}) == (
        "Lake. Severity red. Verify"
    )


def test_build_voice_script_includes_english_and_demo_chichewa():
    script = build_voice_script(
        {"severity": "red", "title": "Lake warning", "action": "Avoid untreated water."}
    )
    assert script["english"].startswith("DEMO English prerecorded voice:")
    assert "CHICHEWA PRERECORDED VOICE DEMO:" in script["chichewa"]
    assert "Lake warning" in script["chichewa"]


def test_no_key_dispatch_appends_exact_payload_without_network(monkeypatch, tmp_path):
    outbox = tmp_path / "alerts_outbox.jsonl"
    monkeypatch.setattr(voice_module, "DEFAULT_ALERTS_OUTBOX", outbox)
    payload = {
        "alert_id": "demo-1",
        "voice": build_voice_script({"severity": "yellow", "title": "Lake", "action": "Verify."}),
    }

    result = dispatch_voice(payload, api_key=None)

    assert result["status"] == "queued"
    assert outbox.read_text(encoding="utf-8") == json.dumps(
        payload, ensure_ascii=False, sort_keys=True
    ) + "\n"
    assert json.loads(outbox.read_text(encoding="utf-8")) == payload
