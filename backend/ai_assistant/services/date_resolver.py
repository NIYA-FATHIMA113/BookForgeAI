from datetime import date, datetime, timedelta


def resolve_booking_date(date_text):
    """
    Converts a booking date into a Python date.

    Supports:
    - YYYY-MM-DD
    - today
    - tomorrow
    - day after tomorrow
    """

    if not date_text:
        return None

    text = date_text.lower().strip()

    today = date.today()

    if text == "today":
        return today

    if text == "tomorrow":
        return today + timedelta(days=1)

    if text == "day after tomorrow":
        return today + timedelta(days=2)

    try:
        return datetime.strptime(
            text,
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return None