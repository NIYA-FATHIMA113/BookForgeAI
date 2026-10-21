from datetime import datetime

from ai_assistant.models import BusinessConfiguration
from .configuration_validator import validate_business_configuration


def normalize_day_list(days):
    """Normalize working-day lists into the project's canonical day labels."""
    if not days:
        return []

    ordered = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    normalized = []
    seen = set()
    for raw in days:
        day = str(raw).strip().capitalize()
        if day == "Monday":
            pass
        # Use a map to survive common casing and punctuation variants.
        day_key = str(raw).strip().lower()
        canonical = {
            "monday": "Monday",
            "tuesday": "Tuesday",
            "wednesday": "Wednesday",
            "thursday": "Thursday",
            "friday": "Friday",
            "saturday": "Saturday",
            "sunday": "Sunday",
        }.get(day_key, raw.strip().title())
        if canonical not in seen:
            seen.add(canonical)
            normalized.append(canonical)

    # Keep the explicit order from the schema; then filter extras.
    ordered_norm = []
    for day in ordered:
        if day in normalized:
            ordered_norm.append(day)
    return ordered_norm


def parse_time_value(value):
    """
    Convert supported AI time strings into a Python time.
    """

    if not value:
        return None

    value = str(value).strip()

    formats = [
        "%H:%M",
        "%I:%M %p",
        "%I %p",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                value,
                fmt,
            ).time()

        except ValueError:
            continue

    raise ValueError(
        f"Invalid time format: {value}"
    )


def update_business_configuration(
    conversation,
    business_info,
):
    """
    Update the business configuration using the
    information extracted from the owner's latest message.

    Existing information is preserved.
    New information is added or merged.
    """

    configuration, created = (
        BusinessConfiguration.objects.get_or_create(
            conversation=conversation
        )
    )

    # -----------------------------------------
    # Business name
    # -----------------------------------------

    if business_info.business_name:
        # Preserve the original extracted name exactly as supplied by the user.
        value = business_info.business_name.strip()
        if value:
            configuration.business_name = value

    # -----------------------------------------
    # Business type
    # -----------------------------------------

    if business_info.business_type:
        normalized_type = str(
            business_info.business_type.strip()
        ).lower()
        # Keep the same normalized internal value used elsewhere.
        from .business_setup import BUSINESS_TYPE_MAPPING
        configuration.business_type = BUSINESS_TYPE_MAPPING.get(
            normalized_type, normalized_type
        )

    if business_info.website_style:
        from tenants.models import Tenant
        allowed_styles = {value for value, _label in Tenant.WEBSITE_STYLES}
        if business_info.website_style in allowed_styles - {"auto"}:
            configuration.website_style = business_info.website_style
            configuration.website_style_suggested = bool(business_info.website_style_suggested)
    elif business_info.website_style_suggested:
        configuration.website_style_suggested = True

    # -----------------------------------------
    # Booking deposit
    # -----------------------------------------

    if business_info.booking_deposit is not None:
        configuration.booking_deposit = (
            business_info.booking_deposit
        )

    # -----------------------------------------
    # Opening time
    # -----------------------------------------

    if business_info.opening_time:
        configuration.opening_time = parse_time_value(
            business_info.opening_time
        )

    # -----------------------------------------
    # Closing time
    # -----------------------------------------

    if business_info.closing_time:
        configuration.closing_time = parse_time_value(
            business_info.closing_time
        )

    # -----------------------------------------
    # Working days
    # -----------------------------------------

    if business_info.working_days:
        configuration.working_days = normalize_day_list(
            business_info.working_days
        )

    # -----------------------------------------
    # Location
    # -----------------------------------------

    if business_info.location:
        configuration.location = (
            business_info.location.strip()
        )

    # -----------------------------------------
    # Contact phone
    # -----------------------------------------

    if business_info.contact_phone:
        configuration.contact_phone = (
            business_info.contact_phone.strip()
        )

    # -----------------------------------------
    # Contact email
    # -----------------------------------------

    if business_info.contact_email:
        configuration.contact_email = (
            business_info.contact_email.strip()
        )

    # -----------------------------------------
    # Booking length
    # -----------------------------------------

    if business_info.booking_length_minutes:
        configuration.booking_length_minutes = (
            business_info.booking_length_minutes
        )

    # -----------------------------------------
    # Number of resources
    # -----------------------------------------

    if business_info.number_of_resources is not None:
        configuration.number_of_resources = (
            business_info.number_of_resources
        )

    # -----------------------------------------
    # Services
    # -----------------------------------------

    if business_info.services:

        existing_services = configuration.services or []
        service_map = {}

        for service in existing_services:
            name = str(service.get("name", "")).strip()
            if name:
                service_map[name.lower()] = service

        for service in business_info.services:
            name = str(service.name).strip()
            if not name:
                continue

            key = name.lower()
            new_service = {
                "name": name,
                "price": service.price,
                "duration_minutes": service.duration_minutes,
            }

            if key in service_map:
                existing = service_map[key]
                if service.price is not None:
                    existing["price"] = service.price
                if service.duration_minutes is not None:
                    existing["duration_minutes"] = service.duration_minutes
            else:
                service_map[key] = new_service

        configuration.services = list(service_map.values())

    # -----------------------------------------
    # Determine completion
    # -----------------------------------------

    validation = validate_business_configuration(
        configuration
    )

    configuration.is_complete = (
        validation["is_complete"]
    )

    configuration.save()

    return configuration
