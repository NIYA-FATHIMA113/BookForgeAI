import os
import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from datetime import date, time

from tenants.models import Tenant
from services.models import Service
from bookings.models import Booking


tenant = Tenant.objects.get(
    business_name="Niya Turf"
)

service = Service.objects.get(
    tenant=tenant,
    name="5-a-side pitch"
)

booking = Booking.objects.create(
    tenant=tenant,
    service=service,
    customer_name="Rahul",
    customer_phone="9876543210",
    booking_date=date(2026, 8, 10),
    booking_time=time(18, 0),
    status="CONFIRMED",
)

print("Booking created successfully!")
print("Booking ID:", booking.id)
print("Customer:", booking.customer_name)
print("Business:", booking.tenant.business_name)
print("Service:", booking.service.name)
print("Date:", booking.booking_date)
print("Time:", booking.booking_time)
print("Status:", booking.status)