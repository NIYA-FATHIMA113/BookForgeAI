from django.db import models
from tenants.models import Tenant


class BusinessHours(models.Model):
    DAYS = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="business_hours"
    )

    day_of_week = models.IntegerField(choices=DAYS)

    opening_time = models.TimeField()

    closing_time = models.TimeField()

    is_closed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("tenant", "day_of_week")

    def __str__(self):
        return f"{self.tenant.business_name} - {self.get_day_of_week_display()}"