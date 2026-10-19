import os
import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

django.setup()

from ai_assistant.services.booking_ai import process_booking_request


message = """
Hi, I want to book Niya Turf tomorrow at 9 PM
for one hour. My name is Rahul and my phone number
is 9876543210. I want the 5-a-side pitch.
"""

result = process_booking_request(message)

print("Success:", result["success"])
print("Result:", result)