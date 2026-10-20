from rest_framework import serializers
from PIL import Image, UnidentifiedImageError

from .models import Tenant

MAX_BUSINESS_IMAGE_SIZE = 8 * 1024 * 1024
ALLOWED_BUSINESS_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_business_image(upload):
    if upload.size > MAX_BUSINESS_IMAGE_SIZE:
        raise serializers.ValidationError("Images must be 8 MB or smaller.")
    try:
        image = Image.open(upload)
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        raise serializers.ValidationError("Upload a valid JPEG, PNG, or WebP image.")
    finally:
        upload.seek(0)
    if image.format not in ALLOWED_BUSINESS_IMAGE_FORMATS:
        raise serializers.ValidationError("Upload a valid JPEG, PNG, or WebP image.")
    return upload


class TenantSerializer(serializers.ModelSerializer):

    logo_image = serializers.ImageField(required=False, allow_null=True)
    hero_image = serializers.ImageField(required=False, allow_null=True)

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
            "business_name_size",
            "logo_image",
            "hero_image",
            "logo_image_external_url",
            "hero_image_external_url",
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

    def validate_business_name_size(self, value):
        if not 16 <= value <= 48:
            raise serializers.ValidationError("Business name size must be between 16 and 48 pixels.")
        return value

    def validate_logo_image(self, value):
        return validate_business_image(value) if value else value

    def validate_hero_image(self, value):
        return validate_business_image(value) if value else value

    def validate_logo_image_external_url(self, value):
        return self.validate_external_image_url(value)

    def validate_hero_image_external_url(self, value):
        return self.validate_external_image_url(value)

    @staticmethod
    def validate_external_image_url(value):
        value = value.strip()
        if value and not value.lower().startswith(("https://", "http://")):
            raise serializers.ValidationError("Use a complete HTTP or HTTPS image URL.")
        return value

    def update(self, instance, validated_data):
        if validated_data.get("logo_image"):
            validated_data["logo_image_external_url"] = ""
        if validated_data.get("hero_image"):
            validated_data["hero_image_external_url"] = ""
        return super().update(instance, validated_data)
