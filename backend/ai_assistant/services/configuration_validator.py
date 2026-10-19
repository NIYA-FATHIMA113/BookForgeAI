def validate_business_configuration(configuration):
    """
    Check whether the AI has collected enough information
    to create the business booking platform.

    Returns:
        {
            "is_complete": bool,
            "missing_fields": list[str]
        }
    """

    missing_fields = []

    # Required business information
    if not configuration.business_name:
        missing_fields.append("business_name")

    if not configuration.business_type:
        missing_fields.append("business_type")

    business_type = (configuration.business_type or "").strip().lower()

    # Services are required for appointment businesses. Restaurants and turf
    # businesses can be created around their bookable tables/pitches alone.
    if business_type not in {"restaurant", "sports_turf"} and not configuration.services:
        missing_fields.append("services")

    # Business hours
    if not configuration.opening_time:
        missing_fields.append("opening_time")

    if not configuration.closing_time:
        missing_fields.append("closing_time")

    # Working days
    if not configuration.working_days:
        missing_fields.append("working_days")

    # Resources
    if not configuration.number_of_resources:
        missing_fields.append("number_of_resources")

    return {
        "is_complete": len(missing_fields) == 0,
        "missing_fields": missing_fields,
    }
