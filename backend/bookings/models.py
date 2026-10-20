
from django.db import models

from tenants.models import Tenant
from services.models import Service, Resource


class Booking(models.Model):
    OCCASIONS = [
        ("regular", "Regular dining"),
        ("birthday", "Birthday"),
        ("anniversary", "Anniversary"),
    ]
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    customer_name = models.CharField(
        max_length=100
    )

    customer_phone = models.CharField(
        max_length=15
    )

    party_size = models.PositiveSmallIntegerField(default=1)

    occasion = models.CharField(max_length=20, choices=OCCASIONS, default="regular")

    booking_date = models.DateField()

    booking_time = models.TimeField()

    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="bookings"
    )

    resource = models.ForeignKey(
        Resource,
        on_delete=models.PROTECT,
        related_name="bookings",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.customer_name} - {self.tenant.business_name}"
