from ai_assistant.services.date_resolver import resolve_booking_date


print("Today:")
print(resolve_booking_date("today"))

print("Tomorrow:")
print(resolve_booking_date("tomorrow"))

print("Day after tomorrow:")
print(resolve_booking_date("day after tomorrow"))

print("Specific date:")
print(resolve_booking_date("2026-08-15"))