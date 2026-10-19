from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer_name",
        "customer_phone",
        "tenant",
        "service",
        "resource",
        "booking_date",
        "booking_time",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "booking_date",
        "tenant",
        "service",
    )

    search_fields = (
        "customer_name",
        "customer_phone",
        "tenant__business_name",
        "service__name",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "-booking_date",
        "-booking_time",
    )