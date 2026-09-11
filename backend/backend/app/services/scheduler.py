from datetime import timedelta


def feasible_slots(earliest, latest, duration_minutes, bookings, buffer_minutes=30, transit_minutes=0):
    duration = timedelta(minutes=duration_minutes)
    gap = timedelta(minutes=buffer_minutes + transit_minutes)
    cursor = earliest
    result = []

    for booking in sorted(bookings, key=lambda x: x.start_time):
        if cursor + duration <= booking.start_time:
            result.append({
                "start_time": cursor,
                "end_time": cursor + duration,
                "buffer_minutes": buffer_minutes,
                "transit_minutes": transit_minutes,
            })
        cursor = max(cursor, booking.end_time + gap)

    if cursor + duration <= latest:
        result.append({
            "start_time": cursor,
            "end_time": cursor + duration,
            "buffer_minutes": buffer_minutes,
            "transit_minutes": transit_minutes,
        })

    return result
