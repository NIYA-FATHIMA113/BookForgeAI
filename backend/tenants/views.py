

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Tenant
from .serializers import TenantSerializer
from availability.models import BusinessHours


class PublicTenantDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tenant = get_object_or_404(Tenant, slug=slug, is_active=True)
        hours = BusinessHours.objects.filter(tenant=tenant).order_by("day_of_week")
        return Response({
            "id": tenant.id,
            "business_name": tenant.business_name,
            "business_type": tenant.business_type,
            "website_style": tenant.website_style,
            "website_template": tenant.website_template,
            "website_font": tenant.website_font,
            "business_name_font": tenant.business_name_font,
            "logo_image": request.build_absolute_uri(tenant.logo_image.url) if tenant.logo_image else None,
            "hero_image": request.build_absolute_uri(tenant.hero_image.url) if tenant.hero_image else None,
            "instagram_handle": tenant.instagram_handle,
            "whatsapp_number": tenant.whatsapp_number,
            "facebook_id": tenant.facebook_id,
            "location": tenant.location,
            "contact_phone": tenant.contact_phone,
            "contact_email": tenant.contact_email,
            "business_hours": [
                {
                    "day_of_week": item.day_of_week,
                    "day": item.get_day_of_week_display(),
                    "opening_time": item.opening_time.strftime("%H:%M"),
                    "closing_time": item.closing_time.strftime("%H:%M"),
                    "is_closed": item.is_closed,
                }
                for item in hours
            ],
        })


class TenantListCreateView(generics.ListCreateAPIView):

    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tenant.objects.filter(
            owner=self.request.user
        ).order_by("-created_at", "-id")

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user
        )


class TenantDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tenant.objects.filter(
            owner=self.request.user
        )
