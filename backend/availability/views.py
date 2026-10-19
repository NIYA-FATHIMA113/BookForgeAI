from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from tenants.models import Tenant

from .models import BusinessHours
from .serializers import BusinessHoursSerializer


class BusinessHoursListCreateView(generics.ListCreateAPIView):

    serializer_class = BusinessHoursSerializer
    permission_classes = [IsAuthenticated]

    def get_tenant(self):
        return get_object_or_404(
            Tenant,
            id=self.kwargs["tenant_id"],
            owner=self.request.user
        )

    def get_queryset(self):
        return BusinessHours.objects.filter(
            tenant=self.get_tenant()
        ).order_by("day_of_week")

    def paginate_queryset(self, queryset):
        # Business hours always have only 7 days.
        # Return all days instead of paginating them.
        return None

    def perform_create(self, serializer):

        serializer.save(
            tenant=self.get_tenant()
        )

class BusinessHoursDetailView(
    generics.RetrieveUpdateDestroyAPIView
):

    serializer_class = BusinessHoursSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return BusinessHours.objects.filter(
            tenant__owner=self.request.user
        )