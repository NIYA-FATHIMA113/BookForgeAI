from rest_framework import serializers

from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        business_type = attrs.get("business_type", getattr(self.instance, "business_type", ""))
        website_template = attrs.get("website_template", getattr(self.instance, "website_template", "auto"))
        template_prefix = "sports" if business_type == "sports_turf" else business_type
        if website_template != "auto" and not website_template.startswith(f"{template_prefix}_"):
            raise serializers.ValidationError({"website_template": "Choose a template for this business type."})
        return attrs

    class Meta:
        model = Tenant

        fields = [
            "id",
            "business_name",
            "slug",
            "business_type",
            "website_style",
            "website_template",
            "website_font",
            "business_name_font",
            "logo_image",
            "hero_image",
            "instagram_handle",
            "whatsapp_number",
            "facebook_id",
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
