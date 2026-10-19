from datetime import datetime, timedelta


def generate_time_slots(
    opening_time,
    closing_time,
    duration,
):
    slots = []

    current = datetime.combine(
        datetime.today(),
        opening_time
    )

    closing = datetime.combine(
        datetime.today(),
        closing_time
    )

    while current + timedelta(minutes=duration) <= closing:
        slots.append(current.time())
        current += timedelta(minutes=duration)

    return slots