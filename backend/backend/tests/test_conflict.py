from datetime import datetime
from app.services.conflict import overlaps


def test_overlap():
    assert overlaps(
        datetime(2026, 9, 11, 10),
        datetime(2026, 9, 11, 12),
        datetime(2026, 9, 11, 11),
        datetime(2026, 9, 11, 13),
    )


def test_touching_intervals_do_not_overlap():
    assert not overlaps(
        datetime(2026, 9, 11, 10),
        datetime(2026, 9, 11, 12),
        datetime(2026, 9, 11, 12),
        datetime(2026, 9, 11, 13),
    )
