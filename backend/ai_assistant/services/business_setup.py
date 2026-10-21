from django.db import transaction
from django.utils.text import slugify

from tenants.models import Tenant
from services.models import Service, Resource
from availability.models import BusinessHours


# --------------------------------
# Business type mapping
# --------------------------------

BUSINESS_TYPE_MAPPING = {
    # Turf aliases and the canonical normalized token.
    "football turf": "sports_turf",
    "football_turf": "sports_turf",
    "sports turf": "sports_turf",
    "sports_turf": "sports_turf",
    "turf": "sports_turf",
    "football ground": "sports_turf",
    "football pitch": "sports_turf",
    "sports facility": "sports_turf",

    # Salon
    "salon": "salon",
    "beauty salon": "salon",
    "hair salon": "salon",
    "barber shop": "salon",
    "barbershop": "salon",

    # Dental clinic
    "dental clinic": "clinic",
    "dentist": "clinic",
    "dental": "clinic",

    # Restaurant
    "restaurant": "restaurant",
    "cafe": "restaurant",
    "coffee shop": "restaurant",
}
# --------------------------------
# Day mapping
# --------------------------------

DAY_MAPPING = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


@transaction.atomic
def create_business_from_configuration(
    configuration,
    owner,
    services_data,
    website_style="auto",
    website_font="classic",
    business_name_font="editorial",
    website_template="auto",
):
    """
    Convert confirmed AI business configuration
    into actual booking-system records.

    Creates/updates:

        Tenant
        Services
        Resources
        Business Hours
    """

    # --------------------------------
    # 1. Validate business information
    # --------------------------------

    if not configuration.business_name:
        raise ValueError("Business name is required.")

    if not configuration.business_type:
        raise ValueError("Business type is required.")

    business_type = BUSINESS_TYPE_MAPPING.get(
        configuration.business_type.lower()
    )

    if not business_type:
        raise ValueError(
            f"Unsupported business type: "
            f"{configuration.business_type}"
        )

    allowed_styles = {value for value, _label in Tenant.WEBSITE_STYLES}
    if website_style not in allowed_styles:
        raise ValueError("Choose a supported website style.")
    allowed_fonts = {value for value, _label in Tenant.WEBSITE_FONTS}
    if website_font not in allowed_fonts:
        raise ValueError("Choose a supported website font.")
    if business_name_font not in allowed_fonts:
        raise ValueError("Choose a supported business name font.")
    allowed_templates = {value for value, _label in Tenant.WEBSITE_TEMPLATES}
    if website_template not in allowed_templates:
        raise ValueError("Choose a supported website template.")
    template_prefix = "sports" if business_type == "sports_turf" else business_type
    if website_template != "auto" and not website_template.startswith(f"{template_prefix}_"):
        raise ValueError("Choose a template for this type of business.")

    # --------------------------------
    # 2. Create / update Tenant
    # --------------------------------

    tenant = Tenant.objects.filter(
        owner=owner,
        business_name=configuration.business_name,
    ).first()
    if tenant is None:
        base_slug = slugify(configuration.business_name) or "business"
        slug = base_slug
        suffix = 2
        while Tenant.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        tenant = Tenant(
            owner=owner,
            business_name=configuration.business_name,
            slug=slug,
        )
    tenant.business_type = business_type
    tenant.website_style = website_style
    tenant.website_font = website_font
    tenant.business_name_font = business_name_font
    tenant.website_template = website_template
    tenant.location = configuration.location or ""
    tenant.contact_phone = configuration.contact_phone or ""
    tenant.contact_email = configuration.contact_email or ""
    tenant.booking_length_minutes = configuration.booking_length_minutes
    tenant.booking_deposit = configuration.booking_deposit
    tenant.is_active = True
    tenant.save()

    # --------------------------------
    # 3. Create / update Services
    # --------------------------------

    if tenant.business_type == "restaurant":
        Service.objects.filter(tenant=tenant).update(is_bookable=False)

    for service_data in services_data:

        # BusinessConfiguration stores services
        # as dictionaries.

        service_name = service_data.get("name")

        if not service_name:
            continue

        duration = (
            service_data.get("duration_minutes")
            or configuration.booking_length_minutes
            or 60
        )

        price = service_data.get("price")

        if price is None:
            price = 0

        is_restaurant = tenant.business_type == "restaurant"
        Service.objects.update_or_create(
            tenant=tenant,
            name=service_name,
            defaults={
                "duration": duration,
                "price": price,
                "is_active": True,
                "description": service_data.get("description", ""),
                "category": service_data.get("category", ""),
                "is_bookable": not is_restaurant,
            },
        )

    if tenant.business_type == "restaurant":
        Service.objects.update_or_create(
            tenant=tenant,
            name="Table reservation",
            defaults={
                "duration": configuration.booking_length_minutes or 90,
                "price": 0,
                "description": "Reserve a table for your party.",
                "category": "Reservations",
                "is_bookable": True,
                "is_active": True,
            },
        )

    # --------------------------------
    # 4. Create tenant-level Resources
    # --------------------------------

    number_of_resources = configuration.number_of_resources or 1

    for resource_number in range(1, number_of_resources + 1):
        Resource.objects.get_or_create(
            tenant=tenant,
            name=f"Resource {resource_number}",
            defaults={"is_active": True, "capacity": 4},
        )

    # --------------------------------
    # 5. Create Business Hours
    # --------------------------------
    working_days = (
        configuration.working_days
        or []
    )

    open_days = set()

    for day_name in working_days:

        day_name = str(day_name).strip().lower()

        day_number = None

        for mapped_day, number in DAY_MAPPING.items():

            if str(mapped_day).strip().lower() == day_name:
                day_number = number
                break

        if day_number is None:
            continue

        open_days.add(day_number)

        BusinessHours.objects.update_or_create(
            tenant=tenant,
            day_of_week=day_number,
            defaults={
                "opening_time": configuration.opening_time,
                "closing_time": configuration.closing_time,
                "is_closed": False,
            },
        )

    # Keep records consistent if the owner revises days/resources before
    # confirming again. Existing bookings retain their resource FK, so don't
    # delete resources that are already referenced.
    BusinessHours.objects.filter(tenant=tenant).exclude(
        day_of_week__in=open_days
    ).delete()
    resource_names = [f"Resource {number}" for number in range(1, number_of_resources + 1)]
    Resource.objects.filter(tenant=tenant).exclude(name__in=resource_names).exclude(
        bookings__isnull=False
    ).delete()

    # --------------------------------
    # 7. Return Tenant
    # --------------------------------

    return tenant
