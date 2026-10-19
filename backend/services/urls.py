from django.urls import path
from .views import (
    ServiceListCreateView,
    ServiceDetailView,
    PublicServiceListView,
    ResourceListCreateView,
    ResourceDetailView,
)

urlpatterns = [
    path(
        "tenants/<int:tenant_id>/services/",
        ServiceListCreateView.as_view(),
        name="service-list-create",
    ),

    path(
        "services/<int:pk>/",
        ServiceDetailView.as_view(),
        name="service-detail",
    ),

    path(
        "book/<slug:slug>/services/",
        PublicServiceListView.as_view(),
        name="public-service-list",
    ),
    path(
        "tenants/<int:tenant_id>/resources/",
        ResourceListCreateView.as_view(),
        name="resource-list-create",
    ),

    # Backwards-compatible alias. Resources returned here belong to the
    # service's tenant, never to the service itself.
    path(
        "services/<int:service_id>/resources/",
        ResourceListCreateView.as_view(),
        name="service-resource-list-create",
    ),

    path(
        "resources/<int:pk>/",
        ResourceDetailView.as_view(),
        name="resource-detail",
    ),
]
