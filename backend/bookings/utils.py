from datetime import datetime, timedelta

from availability.models import BusinessHours
from bookings.models import Booking


def get_business_hours(tenant, booking_date):
    """
    Returns the BusinessHours object for the booking date.
    Returns None if no schedule exists.
    """

    day = booking_date.weekday()

    try:
        return BusinessHours.objects.get(
            tenant=tenant,
            day_of_week=day
        )
    except BusinessHours.DoesNotExist:
        return None


def is_within_business_hours(
    business_hours,
    booking_time,
    duration,
):
    """
    Returns True if the booking starts and ends
    within business hours.
    """

    booking_start = datetime.combine(
        datetime.min,
        booking_time
    )

    booking_end = (
        booking_start +
        timedelta(minutes=duration)
    )

    opening = datetime.combine(
        datetime.min,
        business_hours.opening_time
    )

    closing = datetime.combine(
        datetime.min,
        business_hours.closing_time
    )

    return (
        booking_start >= opening
        and booking_end <= closing
    )


def has_booking_conflict(
    resource,
    booking_date,
    booking_time,
    duration,
):
    """
    Returns True if the specific resource already has
    an overlapping booking.
    """

    new_start = datetime.combine(
        booking_date,
        booking_time
    )

    new_end = new_start + timedelta(
        minutes=duration
    )

    bookings = Booking.objects.filter(
        resource=resource,
        booking_date=booking_date
    ).exclude(
        status="CANCELLED"
    )

    for booking in bookings:

        existing_start = datetime.combine(
            booking.booking_date,
            booking.booking_time
        )

        existing_end = existing_start + timedelta(
            minutes=booking.service.duration
        )

        if (
            new_start < existing_end
            and new_end > existing_start
        ):
            return True

    return False