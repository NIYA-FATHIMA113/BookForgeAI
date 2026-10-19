from django.urls import path
from .views import RecentBookingsView

urlpatterns = [
    path(
        "recent-bookings/",
        RecentBookingsView.as_view(),
        name="recent-bookings",
    ),
]