from ai_assistant.services.ai_provider import extract_booking_request


text = """
Hi, I want to book Niya Turf tomorrow at 6 PM
for one hour. My name is Rahul and my phone number
is 9876543210. I want the 5-a-side pitch.
"""


result = extract_booking_request(text)

print(result)

print("Business:", result.business_name)
print("Date:", result.booking_date)
print("Time:", result.booking_time)
print("Duration:", result.duration_minutes)
print("Service:", result.service_name)
print("Customer:", result.customer_name)
print("Phone:", result.customer_phone)