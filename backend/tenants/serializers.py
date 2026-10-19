from rest_framework import serializers

from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tenant

        fields = [
            "id",
            "business_name",
            "slug",
            "business_type",
            "website_style",
            "location",
            "contact_phone",
            "contact_email",
            "booking_length_minutes",
            "booking_deposit",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "slug",
            "created_at",
            "updated_at",
        ]

    def validate_booking_length_minutes(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError(
                "Booking length must be greater than 0."
            )

        return value

    def validate_booking_deposit(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError(
                "Booking deposit cannot be negative."
            )

        return value
