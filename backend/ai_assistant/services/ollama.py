from ollama import chat

from ai_assistant.schemas import (
    BusinessInfo,
    BookingRequest,
)


MODEL = "llama3.1:8b"


SYSTEM_INSTRUCTION = """
You are the BookForge AI business setup assistant.

Your job is to help business owners create and configure
their online booking platform.

You should:

- Understand what type of business the owner operates.
- Ask useful questions about their business.
- Collect business name, business type, services,
  prices, durations, business hours, and working days.
- Collect the number of independently bookable resources,
  such as pitches, rooms, chairs, doctors, courts, tables,
  or other resources.
- Collect booking requirements such as booking duration,
  deposit, payment requirements, and booking rules.
- Do not invent information that the owner has not provided.
- Ask relevant questions when information is missing.
- Keep responses clear and conversational.
"""


def generate_ai_response(conversation_history):

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTION,
            },
            *conversation_history,
        ],
    )

    return response.message.content

def extract_business_info(text):

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are a structured data extraction assistant for BookForge AI.

Extract ONLY information explicitly provided by the business owner.

Rules:

- Never invent information.
- If information is missing, return null or an empty list.
- Extract every service mentioned by the owner.
- Each service must have:
  - name
  - price if provided
  - duration_minutes if provided
- If the owner gives a price but does not specify a duration,
  do not invent a duration.
- If the owner gives a duration but does not specify a price,
  do not invent a price.
- Preserve the meaning of the owner's information.
- Do not extract information from assumptions or examples.

IMPORTANT TIME FORMAT RULE:

Business hours must ALWAYS be returned as separate
24-hour HH:MM values.

Examples:

"6 AM to 11 PM"
opening_time = "06:00"
closing_time = "23:00"

"9 AM to 7 PM"
opening_time = "09:00"
closing_time = "19:00"

"10:30 AM to 8:30 PM"
opening_time = "10:30"
closing_time = "20:30"

Never put a complete time range inside opening_time
or closing_time.

opening_time must contain ONLY the opening time.

closing_time must contain ONLY the closing time.

For example, this is WRONG:

opening_time = "6 AM to 11 PM"

This is CORRECT:

opening_time = "06:00"
closing_time = "23:00"
""",
            },
            {
                "role": "user",
                "content": f"""
Extract the business information from this business owner's message:

{text}
""",
            },
        ],
        format=BusinessInfo.model_json_schema(),
        options={
            "temperature": 0,
        },
    )

    return BusinessInfo.model_validate_json(
        response.message.content
    )

def extract_booking_request(text):

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": f"""
Extract booking information from the following message.

Only extract information that the customer actually provided.

Do not invent missing information.

If a value is not provided, return null.

Convert dates to YYYY-MM-DD format when possible.
Convert times to 24-hour HH:MM format when possible.

Customer message:

{text}
""",
            }
        ],
        format=BookingRequest.model_json_schema(),
        options={
            "temperature": 0,
        },
    )

    return BookingRequest.model_validate_json(
        response.message.content
    )