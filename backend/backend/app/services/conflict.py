def overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def conflicts(db, Booking, resource_id, start_time, end_time):
    bookings = (
        db.query(Booking)
        .filter(
            Booking.resource_id == resource_id,
            Booking.status.in_(["confirmed", "pending", "reallocated"]),
        )
        .all()
    )
    return [
        b for b in bookings
        if overlaps(start_time, end_time, b.start_time, b.end_time)
    ]
