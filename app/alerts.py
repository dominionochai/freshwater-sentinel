"""Human-readable, bilingual alerts for community water-safety workflows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.models import CommunityProfile, HumanAlert


ALERT_TEMPLATES = {
    "en": {
        "green": {
            "title": "Water watch: low signal",
            "message": "No elevated harmful-algal-bloom signal was detected for {community}. Continue normal precautions and follow local guidance.",
            "action": "No special action is indicated; keep monitoring.",
        },
        "yellow": {
            "title": "Water watch: caution",
            "message": "A possible harmful-algal-bloom signal was detected for {community}. Avoid swimming or drinking untreated water until it is checked locally.",
            "action": "Use caution, keep children and animals away from visibly affected water, and seek local confirmation.",
        },
        "red": {
            "title": "Water watch: high concern",
            "message": "A high harmful-algal-bloom screening signal was detected for {community}. Do not swim, drink untreated water, or harvest food from the affected water.",
            "action": "Keep people and animals away and contact the local health or water authority for confirmation.",
        },
    },
    "sw": {
        "green": {
            "title": "Uangalizi wa maji: ishara ndogo",
            "message": "Hakuna ishara kubwa ya mwani hatari iliyogunduliwa katika {community}. Endelea na tahadhari za kawaida na fuata ushauri wa eneo lako.",
            "action": "Hakuna hatua maalum inayohitajika; endelea kufuatilia.",
        },
        "yellow": {
            "title": "Uangalizi wa maji: tahadhari",
            "message": "Ishara inayoweza kuonyesha mwani hatari imegunduliwa katika {community}. Epuka kuogelea au kunywa maji yasiyotibiwa hadi yakaguliwe na wataalamu wa eneo.",
            "action": "Kuwa mwangalifu, waweke watoto na wanyama mbali na maji yaliyoathirika, na tafuta uthibitisho wa eneo.",
        },
        "red": {
            "title": "Uangalizi wa maji: hatari kubwa",
            "message": "Ishara kubwa ya mwani hatari imegunduliwa katika {community}. Usiogelee, usinywe maji yasiyotibiwa, wala usivune chakula kutoka kwenye maji yaliyoathirika.",
            "action": "Waweke watu na wanyama mbali na maji hayo na wasiliana na mamlaka ya afya au maji kwa uthibitisho.",
        },
    },
}


def _risk_label(value: Any) -> str:
    label = value.label if hasattr(value, "label") else value.get("label", "green")
    return label if label in {"green", "yellow", "red"} else "green"


def build_human_alert(
    risk: Mapping[str, Any], profile: CommunityProfile | None = None
) -> HumanAlert:
    """Render the highest-severity screening result for a local community."""
    profile = profile or CommunityProfile()
    severity_order = {"green": 0, "yellow": 1, "red": 2}
    severity = max(
        (_risk_label(value) for value in risk.values()),
        key=lambda label: severity_order[label],
        default="green",
    )
    language = profile.language if profile.language in ALERT_TEMPLATES else "en"
    template = ALERT_TEMPLATES[language][severity]
    community = profile.name
    return HumanAlert(
        severity=severity,
        language=language,
        title=template["title"],
        message=template["message"].format(community=community),
        action=template["action"],
    )
