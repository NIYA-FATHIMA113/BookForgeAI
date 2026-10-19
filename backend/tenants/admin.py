from django.contrib import admin
from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):

    list_display = (
        "business_name",
        "business_type",
        "owner",
        "is_active",
        "created_at",
    )

    list_filter = (
        "business_type",
        "is_active",
    )

    search_fields = (
        "business_name",
        "contact_phone",
        "contact_email",
        "owner__username",
    )

    readonly_fields = (
        "slug",
        "created_at",
        "updated_at",
    )