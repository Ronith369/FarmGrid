from app.models.models import LabourProvider


def total_wage(wage, workers, days):
    return wage * workers * days


def match_providers(db, request):
    providers = (
        db.query(LabourProvider)
        .filter(
            LabourProvider.region.ilike(f"%{request.region}%"),
            LabourProvider.workers_available >= request.workers_required,
            LabourProvider.is_active == True,
        )
        .all()
    )

    if request.preferred_provider_type:
        providers = [p for p in providers if p.provider_type == request.preferred_provider_type]

    return sorted(
        providers,
        key=lambda p: (abs(p.workers_available - request.workers_required), p.daily_wage_per_worker),
    )
