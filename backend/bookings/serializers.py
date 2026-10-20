
from datetime import date, timedelta
from rest_framework import serializers

from .models import Booking
from .utils import (
    get_business_hours,
    is_within_business_hours,
    has_booking_conflict,
)

from datetime import date, datetime


class BookingSerializer(serializers.ModelSerializer):
    resource_name = serializers.CharField(source="resource.name", read_only=True)
    resource_dining_area = serializers.CharField(source="resource.dining_area", read_only=True)
    dining_area = serializers.ChoiceField(choices=["indoor", "outdoor", "rooftop"], required=False, write_only=True)

    class Meta:
        model = Booking

        fields = [
            "id",
            "customer_name",
            "customer_phone",
            "party_size",
            "occasion",
            "dining_area",
            "booking_date",
            "booking_time",
            "service",
            "resource",
            "resource_name",
            "resource_dining_area",
            "status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "resource",
            "status",
            "created_at",
        ]

    def validate(self, attrs):

        tenant = self.context["tenant"]

        service = attrs["service"]

        booking_date = attrs["booking_date"]

        booking_time = attrs["booking_time"]
        # --------------------------------
        # Booking date cannot be in the past
        # --------------------------------
        if booking_date < date.today():
            raise serializers.ValidationError(
                "Booking date cannot be in the past."
            )
        # --------------------------------
        # Booking cannot be more than 30 days in advance.
        # --------------------------------

        max_booking_date = date.today() + timedelta(days=30)

        if booking_date > max_booking_date:
            raise serializers.ValidationError(
                "Bookings can only be made up to 30 days in advance."
            )
        # --------------------------------
        # Booking time cannot be in the past
        # when booking for today
        # --------------------------------

        if booking_date == date.today():

            current_time = datetime.now().time()

            if booking_time <= current_time:
                raise serializers.ValidationError(
                    "Booking time has already passed."
                )
        # --------------------------------
        # 1. Check service belongs to tenant
        # --------------------------------

        if service.tenant != tenant:

            raise serializers.ValidationError(
                "Invalid service selected."
            )
        if not service.is_active:
            raise serializers.ValidationError(
                "This service is currently unavailable."
            )
        if tenant.business_type == "restaurant" and not service.is_bookable:
            raise serializers.ValidationError({"service": "Menu items cannot be booked. Choose table reservation."})
        party_size = attrs.get("party_size", 1)
        occasion = attrs.get("occasion", "regular")
        dining_area = attrs.pop("dining_area", None)
        if party_size < 1:
            raise serializers.ValidationError({"party_size": "Party size must be at least 1."})

        # --------------------------------
        # 2. Get business hours
        # --------------------------------

        business_hours = get_business_hours(
            tenant,
            booking_date
        )

        if business_hours is None:

            raise serializers.ValidationError(
                "Business hours are not configured for this day."
            )

        if business_hours.is_closed:

            raise serializers.ValidationError(
                "Business is closed on this day."
            )

        # --------------------------------
        # 3. Check booking is within hours
        # --------------------------------

        if not is_within_business_hours(
            business_hours,
            booking_time,
            service.duration
        ):

            raise serializers.ValidationError(
                "Booking is outside business hours."
            )

        # --------------------------------
        # 4. Get active resources
        # --------------------------------

        resources = tenant.resources.filter(is_active=True)
        if tenant.business_type == "restaurant":
            resources = resources.filter(capacity__gte=party_size)
            if dining_area:
                resources = resources.filter(dining_area=dining_area)
            if occasion != "regular":
                resources = resources.filter(supports_celebrations=True)
        elif occasion != "regular":
            raise serializers.ValidationError({"occasion": "Celebration bookings are only available for restaurants."})

        if not resources.exists():

            raise serializers.ValidationError(
                "No resources are available for this service."
            )

        # --------------------------------
        # 5. Find an available resource
        # --------------------------------

        available_resource = None

        for resource in resources:

            if not has_booking_conflict(
                resource,
                booking_date,
                booking_time,
                service.duration
            ):

                available_resource = resource
                break

        # --------------------------------
        # 6. All resources are occupied
        # --------------------------------

        if available_resource is None:

            raise serializers.ValidationError(
                "All resources are booked for this time slot."
            )

        # --------------------------------
        # 7. Assign resource
        # --------------------------------

        attrs["resource"] = available_resource

        return attrs
