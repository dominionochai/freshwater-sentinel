"""Optional voice delivery with an offline, durable outbox fallback."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4


class VoiceProvider(Protocol):
    def synthesize(self, text: str) -> Any:
        """Return provider-specific audio data or a provider receipt."""


@dataclass(frozen=True)
class VoiceMessage:
    message_id: str
    text: str
    created_at: str
    status: str = "queued"


class VoiceOutbox:
    """Append-only JSONL queue; safe as a local fallback when voice is offline."""

    def __init__(self, path: str | Path = "data/voice_outbox.jsonl") -> None:
        self.path = Path(path)

    def enqueue(self, text: str) -> VoiceMessage:
        if not text or not text.strip():
            raise ValueError("voice text cannot be empty")
        message = VoiceMessage(uuid4().hex, text.strip(), datetime.now(timezone.utc).isoformat())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(message), sort_keys=True) + "\n")
        return message

    def pending(self) -> list[VoiceMessage]:
        if not self.path.exists():
            return []
        messages: list[VoiceMessage] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                payload = json.loads(line)
                messages.append(VoiceMessage(**payload))
        return [message for message in messages if message.status == "queued"]


def render_alert_voice(alert: dict[str, Any]) -> str:
    """Render a short, privacy-preserving alert; never includes patient records."""
    severity = str(alert.get("severity", "unknown"))
    title = str(alert.get("title", "Freshwater risk update"))
    action = str(alert.get("action", "Verify locally before taking action."))
    return f"{title}. Severity {severity}. {action}"


def deliver_voice(text: str, provider: VoiceProvider | None = None, outbox: VoiceOutbox | None = None) -> dict[str, Any]:
    """Try the explicitly supplied provider, queueing locally on absence/failure."""
    if not text or not text.strip():
        raise ValueError("voice text cannot be empty")
    if provider is not None:
        try:
            receipt = provider.synthesize(text.strip())
            return {"status": "delivered", "text": text.strip(), "receipt": receipt}
        except Exception as exc:  # provider outages must not lose an alert
            queued = (outbox or VoiceOutbox()).enqueue(text)
            return {"status": "queued", "text": queued.text, "message_id": queued.message_id, "fallback_reason": type(exc).__name__}
    queued = (outbox or VoiceOutbox()).enqueue(text)
    return {"status": "queued", "text": queued.text, "message_id": queued.message_id, "fallback_reason": "provider_not_configured"}
