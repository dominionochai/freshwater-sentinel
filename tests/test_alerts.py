from app.alerts import build_human_alert
from app.models import ActivityRisk, CommunityProfile


def test_alert_uses_swahili_template_and_highest_severity():
    alert = build_human_alert(
        {
            "swimming": ActivityRisk(score=0.2, label="yellow", rationale="test"),
            "drinking": ActivityRisk(score=0.9, label="red", rationale="test"),
        },
        CommunityProfile(name="Mto wetu", language="sw"),
    )
    assert alert.language == "sw"
    assert alert.severity == "red"
    assert "Mto wetu" in alert.message
    assert "Usi" in alert.message


def test_green_alert_is_backward_safe_for_empty_risk():
    alert = build_human_alert({}, CommunityProfile(name="River", language="en"))
    assert alert.severity == "green"
    assert "River" in alert.message
