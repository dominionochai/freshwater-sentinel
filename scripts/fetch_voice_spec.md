# Voice specification

The voice layer is intentionally provider-agnostic. `app/voice.py` accepts a small object implementing `synthesize(text)` and never calls an external service by itself. Production wiring can inject an approved provider; tests should inject a mock.

If no provider is configured, or a provider raises, the alert is written as one JSON object per line to `data/voice_outbox.jsonl` (or to the caller-supplied path). The fallback is durable and contains only the rendered alert text, timestamp, message ID, and queue status. It does not fabricate audio, provider receipts, or health data.

Example:

```python
from app.voice import VoiceOutbox, deliver_voice, render_alert_voice

outbox = VoiceOutbox("data/voice_outbox.jsonl")
text = render_alert_voice({"severity": "yellow", "title": "Lake update", "action": "Verify locally."})
result = deliver_voice(text, provider=None, outbox=outbox)
```

The public integration boundary is `VoiceProvider.synthesize`. Keep retries, credentials, and provider-specific audio handling outside the core package. Queue delivery should be replayed only after a human-approved provider is configured.
