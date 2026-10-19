from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from bookings.models import Booking
from bookings.serializers import BookingSerializer


class RecentBookingsView(generics.ListAPIView):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(
            tenant__owner=self.request.user
        ).select_related(
            "tenant",
            "service",
            "resource"
        ).order_by(
            "-created_at"
        )[:10]