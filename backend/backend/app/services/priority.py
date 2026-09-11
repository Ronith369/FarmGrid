from datetime import datetime, timezone


def waiting_score(created_at):
    if not created_at:
        return 0
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    hours = max(0, (datetime.now(timezone.utc) - created_at).total_seconds() / 3600)
    return min(15, int(hours))


def priority(request):
    # Use an explicitly supplied waiting score when a request/test already has one;
    # otherwise calculate it from queue age.
    wait = getattr(request, "waiting_score", None)
    if wait is None:
        wait = waiting_score(getattr(request, "created_at", None))
    wait = max(0, min(15, int(wait)))
    total = (
        request.urgency_score
        + request.weather_risk_score
        + request.crop_readiness_score
        + wait
        + request.logistics_score
        + request.resource_constraints_score
    )

    reasons = []
    if request.urgency_score >= 18:
        reasons.append("high urgency")
    if request.weather_risk_score >= 18:
        reasons.append("high weather risk")
    if request.crop_readiness_score >= 15:
        reasons.append("crop readiness")
    if wait >= 10:
        reasons.append("long waiting time")
    if request.logistics_score >= 7:
        reasons.append("good logistics")
    if request.resource_constraints_score >= 4:
        reasons.append("strong resource match")

    explanation = (
        "Prioritized because " + ", ".join(reasons)
        if reasons else "Priority is based on the six FarmGrid scoring factors."
    )

    return {
        "urgency": request.urgency_score,
        "weather_risk": request.weather_risk_score,
        "crop_readiness": request.crop_readiness_score,
        "queue_waiting": wait,
        "distance_logistics": request.logistics_score,
        "resource_constraints": request.resource_constraints_score,
        "total": max(0, min(100, total)),
        "explanation": explanation,
    }
