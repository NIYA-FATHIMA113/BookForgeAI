from datetime import date, datetime, timedelta

from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.models import Tenant
from availability.models import BusinessHours

from .models import Booking
from .serializers import BookingSerializer
from .utils import has_booking_conflict


# ==================================================
# PUBLIC BOOKING CREATION
# ==================================================

class BookingCreateView(generics.CreateAPIView):

    serializer_class = BookingSerializer
    permission_classes = [AllowAny]

    def get_tenant(self):

        return get_object_or_404(
            Tenant,
            slug=self.kwargs["slug"],
            is_active=True
        )

    def get_serializer_context(self):

        context = super().get_serializer_context()

        context["tenant"] = self.get_tenant()

        return context

    def perform_create(self, serializer):

        serializer.save(
            tenant=self.get_tenant()
        )


# ==================================================
# OWNER - BOOKING LIST
# ==================================================

class BookingListView(generics.ListAPIView):

    permission_classes = [IsAuthenticated]
    serializer_class = BookingSerializer

    def get_queryset(self):

        queryset = Booking.objects.filter(
            tenant__owner=self.request.user
        ).select_related(
            "service",
            "resource",
            "tenant",
        )

        booking_date = self.request.query_params.get("date")
        customer = self.request.query_params.get("customer")
        service = self.request.query_params.get("service")
        booking_status = self.request.query_params.get("status")
        resource = self.request.query_params.get("resource")

        if booking_date:

            queryset = queryset.filter(
                booking_date=booking_date
            )

        if customer:

            queryset = queryset.filter(
                customer_name__icontains=customer
            )

        if service:

            queryset = queryset.filter(
                service_id=service
            )

        if booking_status:

            queryset = queryset.filter(
                status=booking_status.upper()
            )

        if resource:

            queryset = queryset.filter(
                resource_id=resource
            )

        return queryset.order_by(
            "booking_date",
            "booking_time"
        )

    def list(self, request, *args, **kwargs):

        queryset = self.filter_queryset(
            self.get_queryset()
        )

        data = []

        for booking in queryset:

            data.append({

                "id": booking.id,

                "customer_name":
                    booking.customer_name,

                "customer_phone":
                    booking.customer_phone,

                "tenant": {
                    "id": booking.tenant.id,
                    "business_name": booking.tenant.business_name,
                },

                "booking_date":
                    booking.booking_date,

                "booking_time":
                    booking.booking_time,

                "service": {

                    "id":
                        booking.service.id,

                    "name":
                        booking.service.name,

                    "price":
                        float(
                            booking.service.price
                        ),

                    "duration":
                        booking.service.duration,
                },

                "resource": (

                    {
                        "id":
                            booking.resource.id,

                        "name":
                            booking.resource.name,
                    }

                    if booking.resource

                    else None
                ),

                "status":
                    booking.status,

                "created_at":
                    booking.created_at,
            })

        return Response({

            "count":
                len(data),

            "results":
                data,
        })


# ==================================================
# OWNER - DELETE BOOKING
# ==================================================

class BookingDeleteView(generics.DestroyAPIView):

    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Booking.objects.filter(
            tenant__owner=self.request.user
        )


# ==================================================
# OWNER - UPDATE BOOKING STATUS
# ==================================================

class BookingStatusUpdateView(generics.UpdateAPIView):

    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return Booking.objects.filter(
            tenant__owner=self.request.user
        )

    def update(self, request, *args, **kwargs):

        booking = self.get_object()

        new_status = request.data.get(
            "status"
        )

        # Allow lowercase/mixed-case input
        if new_status:

            new_status = new_status.upper()

        allowed_transitions = {
                "PENDING": [
                    "CONFIRMED",
                    "COMPLETED",
                    "CANCELLED",
                ],

                "CONFIRMED": [
                    "PENDING",
                    "COMPLETED",
                    "CANCELLED",
                ],

                "COMPLETED": [
                    "PENDING",
                    "CONFIRMED",
                    "CANCELLED",
                ],

                "CANCELLED": [
                    "PENDING",
                    "CONFIRMED",
                    "COMPLETED",
                ],
            }
        current_status = booking.status

        if new_status not in allowed_transitions.get(
            current_status,
            []
        ):

            return Response(

                {
                    "error": (
                        f"Cannot change booking status "
                        f"from {current_status} "
                        f"to {new_status}."
                    )
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        booking.status = new_status

        booking.save(
            update_fields=[
                "status"
            ]
        )

        return Response(
            BookingSerializer(
                booking
            ).data
        )


# ==================================================
# PUBLIC - AVAILABLE SLOTS
# ==================================================

class AvailableSlotsView(generics.ListAPIView):

    permission_classes = [AllowAny]

    def get(self, request, slug):

        tenant = get_object_or_404(

            Tenant,

            slug=slug,

            is_active=True
        )

        date_string = request.query_params.get(
            "date"
        )

        service_id = request.query_params.get(
            "service"
        )

        if not date_string:

            return Response(

                {
                    "error":
                        "Please provide a date."
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        if not service_id:

            return Response(

                {
                    "error":
                        "Please provide a service."
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------
        # 1. Convert date
        # --------------------------------

        try:

            selected_date = datetime.strptime(

                date_string,

                "%Y-%m-%d"

            ).date()

        except ValueError:

            return Response(

                {
                    "error":
                        "Invalid date format. "
                        "Use YYYY-MM-DD."
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------
        # 2. Reject past dates
        # --------------------------------

        if selected_date < date.today():

            return Response(

                {
                    "error":
                        "Cannot check availability "
                        "for a past date."
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------
        # 3. Maximum booking window
        # --------------------------------

        max_booking_date = (
            date.today()
            + timedelta(days=30)
        )

        if selected_date > max_booking_date:

            return Response(

                {
                    "error":
                        "Availability can only be "
                        "checked up to 30 days "
                        "in advance."
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------
        # 4. Get business hours
        # --------------------------------

        day_of_week = selected_date.weekday()

        business_hours = (
            BusinessHours.objects.filter(

                tenant=tenant,

                day_of_week=day_of_week,

                is_closed=False

            ).first()
        )

        if not business_hours:

            return Response({

                "date":
                    date_string,

                "available_slots":
                    []
            })

        # --------------------------------
        # 5. Get service
        # --------------------------------

        service = get_object_or_404(

            tenant.services,

            id=service_id,

            is_active=True
        )

        # --------------------------------
        # 6. Get active resources
        # --------------------------------

        resources = tenant.resources.filter(is_active=True)

        if not resources.exists():

            return Response(

                {
                    "error":
                        "No resources are "
                        "available for this service."
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------
        # 7. Generate slots
        # --------------------------------

        slots = []

        current_time = datetime.combine(

            selected_date,

            business_hours.opening_time
        )

        closing_time = datetime.combine(

            selected_date,

            business_hours.closing_time
        )

        while (

            current_time
            + timedelta(
                minutes=service.duration
            )
            <= closing_time

        ):

            slot_is_available = False

            # --------------------------------
            # Check every resource
            # --------------------------------

            for resource in resources:

                if not has_booking_conflict(

                    resource,

                    selected_date,

                    current_time.time(),

                    service.duration

                ):

                    slot_is_available = True

                    break

            # --------------------------------
            # Add available slot
            # --------------------------------

            if slot_is_available:

                slots.append(

                    current_time.strftime(
                        "%H:%M"
                    )
                )

            current_time += timedelta(

                minutes=service.duration
            )

        # --------------------------------
        # 8. Response
        # --------------------------------

        return Response({

            "date":
                date_string,

            "service":
                service.name,

            "duration":
                service.duration,

            "available_slots":
                slots
        })


# ==================================================
# PUBLIC - BOOKING DETAILS
# ==================================================

class PublicBookingDetailView(
    generics.RetrieveAPIView
):

    permission_classes = [AllowAny]

    def get(self, request, slug, pk):

        # --------------------------------
        # Get tenant
        # --------------------------------

        tenant = get_object_or_404(

            Tenant,

            slug=slug,

            is_active=True
        )

        # --------------------------------
        # Get customer phone
        # --------------------------------

        phone = request.query_params.get(
            "phone"
        )

        if not phone:

            return Response(

                {
                    "error":
                        "Phone number is required."
                },

                status=status.HTTP_400_BAD_REQUEST
            )

        # --------------------------------
        # Find booking
        # --------------------------------

        booking = get_object_or_404(

            Booking,

            id=pk,

            tenant=tenant,

            customer_phone=phone
        )

        # --------------------------------
        # Response
        # --------------------------------

        return Response({

            "booking_id":
                booking.id,

            "business":
                tenant.business_name,

            "customer_name":
                booking.customer_name,

            "customer_phone":
                booking.customer_phone,

            "service":
                booking.service.name,

            "resource": (

                booking.resource.name

                if booking.resource

                else None
            ),

            "date":
                booking.booking_date,

            "time":
                booking.booking_time,

            "status":
                booking.status,
        })


# ==================================================
# OWNER - DASHBOARD SUMMARY
# ==================================================

class DashboardSummaryView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        bookings = Booking.objects.filter(

            tenant__owner=request.user
        )

        today = date.today()

        today_bookings = bookings.filter(

            booking_date=today
        )

        pending = bookings.filter(

            status="PENDING"
        )

        confirmed = bookings.filter(

            status="CONFIRMED"
        )

        completed = bookings.filter(

            status="COMPLETED"
        )

        cancelled = bookings.filter(

            status="CANCELLED"
        )

        # --------------------------------
        # Revenue
        # --------------------------------

        revenue = 0

        for booking in bookings.filter(

            status__in=[
                "CONFIRMED",
                "COMPLETED"
            ]

        ):

            revenue += booking.service.price

        return Response({

            "total_bookings":
                bookings.count(),

            "today_bookings":
                today_bookings.count(),

            "pending_bookings":
                pending.count(),

            "confirmed_bookings":
                confirmed.count(),

            "completed_bookings":
                completed.count(),

            "cancelled_bookings":
                cancelled.count(),

            "total_revenue":
                revenue,
        })
