from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from tenants.models import Tenant
from services.models import Service, Resource
from availability.models import BusinessHours
from bookings.models import Booking


User = get_user_model()


class BookingCreateAPITest(APITestCase):

    def setUp(self):

        # -----------------------------
        # Create owner
        # -----------------------------

        self.user = User.objects.create_user(
            username="testowner",
            password="testpassword123"
        )

        # -----------------------------
        # Create business
        # -----------------------------

        self.tenant = Tenant.objects.create(
            owner=self.user,
            business_name="Test Turf",
            business_type="sports_turf",
            slug="test-turf",
            is_active=True,
        )

        # -----------------------------
        # Create service
        # -----------------------------

        self.service = Service.objects.create(
            tenant=self.tenant,
            name="5-a-side pitch",
            price=800,
            duration=60,
            is_active=True,
        )

        # -----------------------------
        # Create resource
        # -----------------------------

        self.resource = Resource.objects.create(
            tenant=self.tenant,
            name="Pitch 1",
            is_active=True,
        )

        # -----------------------------
        # Create business hours
        # -----------------------------

        # Monday -> 0
        BusinessHours.objects.create(
            tenant=self.tenant,
            day_of_week=0,
            opening_time=time(9, 0),
            closing_time=time(22, 0),
            is_closed=False,
        )

        # -----------------------------
        # API URL
        # -----------------------------

        self.url = reverse(
            "create-booking",
            kwargs={"slug": self.tenant.slug}
        )

    def next_monday(self):
        days_until_monday = (7 - date.today().weekday()) % 7
        return date.today() + timedelta(days=days_until_monday or 7)

    def test_create_booking_successfully(self):

        # Find next Monday
        today = date.today()

        days_until_monday = (
            7 - today.weekday()
        ) % 7

        if days_until_monday == 0:
            days_until_monday = 7

        booking_date = today + timedelta(
            days=days_until_monday
        )

        data = {
            "customer_name": "Rahul",
            "customer_phone": "9876543210",
            "booking_date": booking_date,
            "booking_time": "18:00",
            "service": self.service.id,
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            201
        )

        self.assertEqual(
            Booking.objects.count(),
            1
        )

        booking = Booking.objects.first()

        self.assertEqual(
            booking.customer_name,
            "Rahul"
        )

        self.assertEqual(
            booking.service,
            self.service
        )

        self.assertEqual(
            booking.resource,
            self.resource
        )

        self.assertEqual(
            booking.status,
            "PENDING"
        )

    def test_different_services_share_resource_availability(self):
        seven_a_side = Service.objects.create(
            tenant=self.tenant, name="7-a-side football", price=1000,
            duration=60, is_active=True,
        )
        booking_date = self.next_monday()
        first_booking = {"customer_name": "Rahul", "customer_phone": "9876543210", "booking_date": booking_date, "booking_time": "18:00", "service": self.service.id}
        second_booking = {"customer_name": "Arjun", "customer_phone": "9999999999", "booking_date": booking_date, "booking_time": "18:00", "service": seven_a_side.id}

        self.assertEqual(self.client.post(self.url, first_booking, format="json").status_code, 201)
        response = self.client.post(self.url, second_booking, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("All resources are booked for this time slot.", str(response.data))

    def test_second_tenant_resource_is_assigned_when_first_is_occupied(self):
        second_resource = Resource.objects.create(
            tenant=self.tenant, name="Pitch 2", is_active=True,
        )
        booking_date = self.next_monday()
        first_booking = {"customer_name": "Rahul", "customer_phone": "9876543210", "booking_date": booking_date, "booking_time": "18:00", "service": self.service.id}
        second_booking = {"customer_name": "Arjun", "customer_phone": "9999999999", "booking_date": booking_date, "booking_time": "18:00", "service": self.service.id}

        self.assertEqual(self.client.post(self.url, first_booking, format="json").status_code, 201)
        self.assertEqual(self.client.post(self.url, second_booking, format="json").status_code, 201)
        self.assertEqual(Booking.objects.order_by("created_at").last().resource, second_resource)

        third_booking = {
            "customer_name": "Meera", "customer_phone": "8888888888",
            "booking_date": booking_date, "booking_time": "18:00",
            "service": self.service.id,
        }
        response = self.client.post(self.url, third_booking, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("All resources are booked for this time slot.", str(response.data))

    def test_available_slots_uses_resources_shared_by_services(self):
        seven_a_side = Service.objects.create(
            tenant=self.tenant, name="7-a-side football", price=1000,
            duration=60, is_active=True,
        )
        second_resource = Resource.objects.create(
            tenant=self.tenant, name="Pitch 2", is_active=True,
        )
        booking_date = self.next_monday()
        Booking.objects.create(
            tenant=self.tenant, customer_name="Rahul", customer_phone="9876543210",
            booking_date=booking_date, booking_time=time(18, 0),
            service=self.service, resource=self.resource,
        )

        response = self.client.get(
            reverse("available-slots", kwargs={"slug": self.tenant.slug}),
            {"date": booking_date.isoformat(), "service": seven_a_side.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("18:00", response.data["available_slots"])

        Booking.objects.create(
            tenant=self.tenant, customer_name="Arjun", customer_phone="9999999999",
            booking_date=booking_date, booking_time=time(18, 0),
            service=seven_a_side, resource=second_resource,
        )
        response = self.client.get(
            reverse("available-slots", kwargs={"slug": self.tenant.slug}),
            {"date": booking_date.isoformat(), "service": seven_a_side.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("18:00", response.data["available_slots"])
    def test_booking_outside_business_hours(self):

        today = date.today()

        days_until_monday = (
            7 - today.weekday()
        ) % 7

        if days_until_monday == 0:
            days_until_monday = 7

        booking_date = today + timedelta(
            days=days_until_monday
        )

        data = {
            "customer_name": "Rahul",
            "customer_phone": "9876543210",
            "booking_date": booking_date,
            "booking_time": "23:00",
            "service": self.service.id,
        }

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            400
        )

        self.assertIn(
            "Booking is outside business hours.",
            str(response.data)
        )

        self.assertEqual(
            Booking.objects.count(),
            0
        )
    def test_double_booking_is_rejected(self):

        today = date.today()

        days_until_monday = (
            7 - today.weekday()
        ) % 7

        if days_until_monday == 0:
            days_until_monday = 7

        booking_date = today + timedelta(
            days=days_until_monday
        )

        data = {
            "customer_name": "Rahul",
            "customer_phone": "9876543210",
            "booking_date": booking_date,
            "booking_time": "18:00",
            "service": self.service.id,
        }

        # First booking
        response1 = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response1.status_code,
            201
        )

        # Second booking for the SAME resource/time
        data["customer_name"] = "Arjun"
        data["customer_phone"] = "9999999999"

        response2 = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response2.status_code,
            400
        )

        self.assertIn(
            "All resources are booked for this time slot.",
            str(response2.data)
        )

        # Only one booking should exist
        self.assertEqual(
            Booking.objects.count(),
            1
        )
