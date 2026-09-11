from types import SimpleNamespace
from app.services.priority import priority


def test_priority_maximum():
    request = SimpleNamespace(
        urgency_score=25,
        weather_risk_score=25,
        crop_readiness_score=20,
        logistics_score=10,
        resource_constraints_score=5,
        waiting_score=15,
        created_at=None,
    )
    assert priority(request)["total"] == 100
