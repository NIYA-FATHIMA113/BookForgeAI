from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny

from tenants.models import Tenant
from .models import Service, Resource
from .serializers import ServiceSerializer, ResourceSerializer

class ServiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_tenant(self):
        return get_object_or_404(
            Tenant,
            id=self.kwargs["tenant_id"],
            owner=self.request.user,
        )

    def get_queryset(self):
        return Service.objects.filter(
            tenant=self.get_tenant()
        )

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.get_tenant()
        )

class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Service.objects.filter(
            tenant__owner=self.request.user
        )

class PublicServiceListView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Service.objects.filter(
            tenant__slug=self.kwargs["slug"],
            tenant__is_active=True,
            is_active=True,
        )
class ResourceListCreateView(generics.ListCreateAPIView):
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]

    def get_tenant(self):
        """Resolve a tenant owned by the current user.

        The service-based URL is retained as a backwards-compatible alias for
        existing clients, but resources are always scoped to that service's
        tenant.
        """
        if "tenant_id" in self.kwargs:
            return get_object_or_404(
                Tenant,
                id=self.kwargs["tenant_id"],
                owner=self.request.user,
            )

        service = get_object_or_404(
            Service,
            id=self.kwargs["service_id"],
            tenant__owner=self.request.user,
        )
        return service.tenant

    def get_queryset(self):
        return Resource.objects.filter(
            tenant=self.get_tenant()
        )

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.get_tenant()
        )


class ResourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ResourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Resource.objects.filter(
            tenant__owner=self.request.user
        )
