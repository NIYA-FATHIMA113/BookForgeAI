from django.urls import path
from .views import TenantListCreateView, TenantDetailView, PublicTenantDetailView

urlpatterns = [
    path("public/<slug:slug>/", PublicTenantDetailView.as_view(), name="public-tenant-detail"),
    path("", TenantListCreateView.as_view(), name="tenant-list-create"),
    path("<int:pk>/", TenantDetailView.as_view(), name="tenant-detail"),
]
