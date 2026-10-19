import os

from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

from ai_assistant.schemas import (
    BusinessInfo,
    BookingRequest,
)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# =========================================================
# BUSINESS SETUP AI
# =========================================================

SYSTEM_INSTRUCTION = """
You are BookForge AI, a business setup assistant.

Your job is to help business owners configure their online booking
platform through a natural, step-by-step conversation.

IMPORTANT CONVERSATION RULES:

1. ALWAYS use information that the business owner has already provided
   in the conversation.

2. NEVER ask the owner for information that they have already provided.

3. Infer the business type from the owner's wording when it is clear.

   Examples:
   - "turf", "football turf", "sports turf", "football ground"
     → Turf / Sports Facility
   - "salon", "beauty salon", "hair salon"
     → Beauty Salon
   - "gym", "fitness center"
     → Gym / Fitness
   - "clinic", "doctor's clinic"
     → Clinic
   - "restaurant", "cafe"
     → Restaurant / Cafe

4. If the owner says something like:
   "I run a turf named FastBoots in Balussery"

   understand that:
   - Business name = FastBoots
   - Business type = Turf / Sports Facility
   - Location = Balussery

   Do NOT ask:
   "What type of business do you operate?"

   Instead, ask only for the information that is still missing.

5. Collect the following information when relevant:

   - Business name
   - Business type
   - Location
   - Services
   - Service prices
   - Service durations
   - Number of independently bookable resources
   - Business hours
   - Working days
   - Booking duration
   - Deposit/payment requirements
   - Booking rules
   - Contact information

6. Different businesses may use different names for resources.

   Examples:
   - Turf → pitches
   - Salon → chairs/stylists
   - Clinic → doctors/rooms
   - Gym → trainers/equipment
   - Restaurant → tables
   - Event venue → halls/rooms

7. NEVER invent information.

   If the owner has not provided something, ask for it.

   NEVER change, rename, paraphrase, or invent a business name.
   If the owner provides a business name, preserve it exactly as provided.

8. Do not repeatedly ask the same question.

9. When the owner provides multiple pieces of information in one message,
   acknowledge and use all of them.

10. Keep responses short, clear, friendly, and conversational.

11. Ask only the next relevant questions instead of asking for everything
    at once.

12. When enough information has been collected, tell the owner that the
    business configuration is ready for confirmation.

Example:

Owner:
"I run a turf named FastBoots in Balussery."

Good response:
"Great! I've got FastBoots, a turf in Balussery. ⚽

I just need a few more details:
- How many pitches do you have?
- What are your booking prices and durations?
- What are your working days and hours?"

Bad response:
"What type of business do you operate?"
"""

def generate_ai_response(conversation_history):

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=conversation_history,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )

    return response.text


def extract_business_info(text):

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"""
Extract business information from the following
business owner's message.

Only extract information that the owner actually provided.

Do not invent missing information.

If information is not provided, return null or an empty list.

IMPORTANT TIME FORMAT RULE:

If the owner provides business hours in natural language,
convert them into separate 24-hour HH:MM values.

For example:

"6 AM to 11 PM"
opening_time = "06:00"
closing_time = "23:00"

"9 AM to 7 PM"
opening_time = "09:00"
closing_time = "19:00"

"10:30 AM to 8:30 PM"
opening_time = "10:30"
closing_time = "20:30"

Never put a range such as "6 AM to 11 PM"
inside opening_time or closing_time.

opening_time must contain ONLY the opening time.

closing_time must contain ONLY the closing time.

Business owner's message:

{text}
""",
        config={
            "response_mime_type": "application/json",
            "response_schema": BusinessInfo,
        },
    )

    return response.parsed
# =========================================================
# BOOKING AI
# =========================================================

def extract_booking_request(text):

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"""
Extract booking information from the following customer message.

Only extract information that the customer actually provided.

Do not invent missing information.

If a value is not provided, return null.

Convert dates to YYYY-MM-DD format when possible.
Convert times to 24-hour HH:MM format when possible.

Customer message:

{text}
""",
        config={
            "response_mime_type": "application/json",
            "response_schema": BookingRequest,
        },
    )

    return response.parsed