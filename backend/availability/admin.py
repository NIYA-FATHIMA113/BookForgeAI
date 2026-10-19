from django.contrib import admin
from .models import BusinessHours


@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):

    list_display = (
        "tenant",
        "day_of_week",
        "opening_time",
        "closing_time",
        "is_closed",
    )

    list_filter = (
        "is_closed",
        "day_of_week",
        "tenant",
    )

    search_fields = (
        "tenant__business_name",
    )