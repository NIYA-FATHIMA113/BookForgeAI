import os

from datetime import time, datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

from bookings.models import Booking
from tenants.models import Tenant
from services.models import Service

from ai_assistant.services.ai_provider import extract_booking_request
from ai_assistant.services.mock_booking_ai import mock_booking_request
from ai_assistant.services.date_resolver import resolve_booking_date

from bookings.utils import (
    get_business_hours,
    is_within_business_hours,
    has_booking_conflict,
)


def get_available_slots(
    tenant,
    service,
    booking_date,
    business_hours,
    duration,
):
    slots = []

    current_time = datetime.combine(
        booking_date,
        business_hours.opening_time
    )

    closing_time = datetime.combine(
        booking_date,
        business_hours.closing_time
    )

    while current_time + timedelta(minutes=duration) <= closing_time:

        slot_time = current_time.time()

        if not has_booking_conflict(
            tenant,
            booking_date,
            slot_time,
            duration,
        ):
            slots.append(
                slot_time.strftime("%H:%M")
            )

        current_time += timedelta(minutes=duration)

    return slots


def process_booking_request(text):

    # --------------------------------
    # Extract booking information
    # --------------------------------

    if os.getenv("USE_MOCK_AI", "false").lower() == "true":
        booking_request = mock_booking_request()
    else:
        booking_request = extract_booking_request(text)

    # --------------------------------
    # Resolve booking date
    # --------------------------------

    booking_date = resolve_booking_date(
        booking_request.booking_date
    )

    if not booking_date:
        return {
            "success": False,
            "error": "Could not understand the booking date."
        }

    # --------------------------------
    # Validate required information
    # --------------------------------

    if not booking_request.business_name:
        return {
            "success": False,
            "error": "Business name is required."
        }

    if not booking_request.service_name:
        return {
            "success": False,
            "error": "Service name is required."
        }

    # --------------------------------
    # Find business
    # --------------------------------

    tenant = Tenant.objects.filter(
        business_name__iexact=booking_request.business_name,
        is_active=True,
    ).first()

    if not tenant:
        return {
            "success": False,
            "error": "Business not found."
        }

    # --------------------------------
    # Find service
    # --------------------------------

    service = Service.objects.filter(
        tenant=tenant,
        name__iexact=booking_request.service_name,
        is_active=True,
    ).first()

    if not service:
        return {
            "success": False,
            "error": "Service not found for this business."
        }

    # --------------------------------
    # Check business hours
    # --------------------------------

    business_hours = get_business_hours(
        tenant,
        booking_date
    )

    if business_hours is None:
        return {
            "success": False,
            "error": "Business hours are not configured for this day."
        }

    if business_hours.is_closed:
        return {
            "success": False,
            "error": "Business is closed on this day."
        }

    # --------------------------------
    # Determine duration
    # --------------------------------

    duration = booking_request.duration_minutes

    if not duration:
        duration = service.duration

    # --------------------------------
    # Check booking time
    # --------------------------------

    if not booking_request.booking_time:
        return {
            "success": False,
            "error": "Booking time is required."
        }

    booking_time = time.fromisoformat(
        booking_request.booking_time
    )

    # --------------------------------
    # Check business hours
    # --------------------------------

    if not is_within_business_hours(
        business_hours,
        booking_time,
        duration,
    ):
        return {
            "success": False,
            "error": "The requested time is outside business hours."
        }

    # --------------------------------
    # Check booking conflict
    # --------------------------------

    if has_booking_conflict(
        tenant,
        booking_date,
        booking_time,
        duration,
    ):

        available_slots = get_available_slots(
            tenant,
            service,
            booking_date,
            business_hours,
            duration,
        )

        return {
            "success": False,
            "error": "This time slot is already booked.",
            "available_slots": available_slots,
        }

    # --------------------------------
    # Everything is available
    # --------------------------------

    booking = Booking.objects.create(
        tenant=tenant,
        service=service,
        customer_name=booking_request.customer_name,
        customer_phone=booking_request.customer_phone,
        booking_date=booking_date,
        booking_time=booking_time,
        status="CONFIRMED",
    )

    return {
        "success": True,
        "booking_id": booking.id,
        "message": "Booking confirmed successfully.",
        "business_name": tenant.business_name,
        "service": service.name,
        "customer_name": booking.customer_name,
        "booking_date": str(booking.booking_date),
        "booking_time": str(booking.booking_time),
        "duration_minutes": duration,
    }