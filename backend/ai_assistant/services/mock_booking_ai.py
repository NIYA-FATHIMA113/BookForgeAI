from ai_assistant.schemas import BookingRequest


def mock_booking_request():
    return BookingRequest(
        business_name="Niya Turf",
        booking_date="2026-08-10",
        booking_time="21:00",
        duration_minutes=60,
        service_name="5-a-side pitch",
        customer_name="Rahul",
        customer_phone="9876543210",
    )