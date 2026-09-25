"""API route exposing the real bilingual alert + voice script builders.

Wires app.alerts.build_human_alert and app.voice.build_voice_script to
HTTP. No new alert or translation content is added here — the English
and Swahili SMS text, and the "DEMO"-labelled Chichewa voice text, are
exactly what those functions already generate.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.alerts import build_human_alert
from app.models import CommunityProfile
from app.voice import build_voice_script

router = APIRouter(prefix="/voice", tags=["voice"])

# A demo-severity risk dict for standalone viewing of this screen (no live
# /analyze result loaded yet). Shape matches ActivityRisk: score/label/
# rationale. Using "red" so the VOICE screen has something to render by
# default; a real risk dict from a live /analyze call overrides this.
_DEMO_RISK: dict[str, dict[str, Any]] = {
    "demo-lake": {
        "score": 0.78,
        "label": "red",
        "rationale": "Elevated NDCI and chlorophyll-a signal in the littoral zone.",
    }
}

# NOTE: CommunityProfile.community defaults to the English string
# "the community", which build_human_alert interpolates verbatim into
# Swahili templates too (producing "...katika the community"). That is a
# real bug in app.alerts, out of scope to fix here — this route works
# around it by always supplying an explicit, real community name so the
# rendered Swahili text is not broken by an English placeholder leaking
# into it.
_DEFAULT_COMMUNITY_NAME = "Demo Lake community"


class VoiceScriptRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    risk: dict[str, Any] = Field(default_factory=lambda: dict(_DEMO_RISK))
    community_profile: CommunityProfile | None = None
    swahili_community_profile: CommunityProfile | None = None


@router.post("/script")
def get_voice_script(request: VoiceScriptRequest) -> dict[str, Any]:
    en_profile = request.community_profile or CommunityProfile(
        language="en", community=_DEFAULT_COMMUNITY_NAME, name=_DEFAULT_COMMUNITY_NAME
    )
    sw_profile = request.swahili_community_profile or CommunityProfile(
        language="sw", community=_DEFAULT_COMMUNITY_NAME, name=_DEFAULT_COMMUNITY_NAME
    )

    en_alert = build_human_alert(request.risk, en_profile)
    sw_alert = build_human_alert(request.risk, sw_profile)
    script = build_voice_script(en_alert.model_dump())

    return {
        "en_alert": en_alert.model_dump(),
        "sw_alert": sw_alert.model_dump(),
        "voice_script": script,
    }
