from app.voice import VoiceOutbox, deliver_voice, render_alert_voice


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
    assert render_alert_voice({"severity": "red", "title": "Lake", "action": "Verify"}) == "Lake. Severity red. Verify"
