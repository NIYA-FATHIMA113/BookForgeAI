
from django.db import models
from tenants.models import Tenant


class Service(models.Model):
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="services"
    )

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    category = models.CharField(max_length=80, blank=True)

    is_bookable = models.BooleanField(default=True)

    duration = models.PositiveIntegerField(
        help_text="Duration in minutes"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.name} ({self.tenant.business_name})"


class Resource(models.Model):
    DINING_AREAS = [
        ("indoor", "Indoor"),
        ("outdoor", "Outdoor"),
        ("rooftop", "Rooftop"),
    ]
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="resources"
    )

    name = models.CharField(
        max_length=100
    )

    capacity = models.PositiveIntegerField(default=4)

    dining_area = models.CharField(max_length=20, choices=DINING_AREAS, default="indoor")

    supports_celebrations = models.BooleanField(default=False)

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.name} - {self.tenant.business_name}"
