from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Tenant(models.Model):

    WEBSITE_STYLES = [
        ("auto", "Match my business type"),
        ("modern", "Modern and minimal"),
        ("warm", "Warm and welcoming"),
        ("bold", "Bold and energetic"),
        ("elegant", "Elegant and premium"),
        ("nature", "Natural and relaxed"),
        ("3d", "3D motion"),
        ("illustrated", "Illustrated"),
        ("playful", "Cartoon pop"),
    ]

    WEBSITE_FONTS = [
        ("classic", "Classic serif"),
        ("modern", "Modern sans serif"),
        ("friendly", "Friendly rounded"),
        ("editorial", "Editorial display"),
        ("mono", "Minimal mono"),
    ]

    WEBSITE_TEMPLATES = [
        ("auto", "Match business type"),
        ("restaurant_classic", "Classic bistro"),
        ("restaurant_modern", "Modern menu"),
        ("restaurant_bistro", "Neighborhood bistro"),
        ("restaurant_market", "Market table"),
        ("salon_editorial", "Editorial studio"),
        ("salon_minimal", "Minimal studio"),
        ("salon_botanical", "Botanical beauty"),
        ("salon_glam", "Glam lounge"),
        ("clinic_calm", "Calm care"),
        ("clinic_modern", "Modern practice"),
        ("clinic_family", "Family clinic"),
        ("clinic_holistic", "Holistic wellness"),
        ("sports_arena", "Arena"),
        ("sports_club", "Sports club"),
        ("sports_field", "Open field"),
        ("sports_night", "Night game"),
    ]

    BUSINESS_TYPES = [
        ("restaurant", "Restaurant"),
        ("salon", "Salon"),
        ("clinic", "Clinic"),
        ("sports_turf", "Sports Turf"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tenants"
    )

    business_name = models.CharField(
        max_length=255
    )

    slug = models.SlugField(
        unique=True
    )

    business_type = models.CharField(
        max_length=30,
        choices=BUSINESS_TYPES
    )

    website_style = models.CharField(
        max_length=20,
        choices=WEBSITE_STYLES,
        default="auto",
    )
    website_template = models.CharField(max_length=30, choices=WEBSITE_TEMPLATES, default="auto")
    website_font = models.CharField(max_length=20, choices=WEBSITE_FONTS, default="classic")
    business_name_font = models.CharField(max_length=20, choices=WEBSITE_FONTS, default="editorial")

    logo_image = models.ImageField(upload_to="businesses/logos/", blank=True, null=True)
    hero_image = models.ImageField(upload_to="businesses/hero/", blank=True, null=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    facebook_id = models.CharField(max_length=200, blank=True)

    # -----------------------------
    # Business contact information
    # -----------------------------

    location = models.CharField(
        max_length=255,
        blank=True
    )

    contact_phone = models.CharField(
        max_length=15,
        blank=True
    )

    contact_email = models.EmailField(
        blank=True
    )

    # -----------------------------
    # Booking configuration
    # -----------------------------

    booking_length_minutes = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    booking_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # -----------------------------
    # Business state
    # -----------------------------

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):

        if not self.slug:
            self.slug = slugify(self.business_name)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.business_name
