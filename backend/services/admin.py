from django.contrib import admin
from .models import Service, Resource


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "tenant",
        "duration",
        "price",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "tenant",
    )

    search_fields = (
        "name",
        "tenant__business_name",
    )


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "tenant",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "tenant",
    )

    search_fields = (
        "name",
        "tenant__business_name",
    )
