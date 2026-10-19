from django.urls import path

from .views import (
    BookingCreateView,
    BookingListView,
    BookingDeleteView,
    BookingStatusUpdateView,
    AvailableSlotsView,
    DashboardSummaryView,
    PublicBookingDetailView,
)

urlpatterns = [
    path(
        "book/<slug:slug>/",
        BookingCreateView.as_view(),
        name="create-booking",
    ),

    path(
        "bookings/",
        BookingListView.as_view(),
        name="booking-list",
    ),

    path(
        "bookings/<int:pk>/",
        BookingDeleteView.as_view(),
        name="booking-delete",
    ),
    path(
        "bookings/<int:pk>/status/",
        BookingStatusUpdateView.as_view(),
        name="booking-status-update",
    ),
    path(
        "book/<slug:slug>/available-slots/",
        AvailableSlotsView.as_view(),
        name="available-slots"
    ),
    path(
        "book/<slug:slug>/booking/<int:pk>/",
        PublicBookingDetailView.as_view(),
        name="public-booking-detail",
    ),
    path(
        "dashboard/summary/",
        DashboardSummaryView.as_view(),
        name="dashboard-summary",
    ),
    ]