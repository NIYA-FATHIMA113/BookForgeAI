import json
import os
import re

from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from google import genai
from google.genai import types

from ai_assistant.schemas import BusinessInfo, BookingRequest, ServiceInfo

load_dotenv()


# =========================================================
# ENVIRONMENT
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-oss-20b",
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


# =========================================================
# CLIENTS
# =========================================================

groq_client = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY
    else None
)

openrouter_client = (
    OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
    )
    if OPENROUTER_API_KEY
    else None
)

gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY)
    if GEMINI_API_KEY
    else None
)


# =========================================================
# GENERAL BOOKFORGE SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are BookForge AI.

BookForge helps small-business owners create and configure
their own online booking platform.

You are assisting the BUSINESS OWNER, not the customer.

Your responsibilities include:

- understanding the owner's business
- collecting business information
- understanding services or facilities
- understanding booking requirements
- understanding business hours
- understanding working days
- understanding bookable resources
- helping configure the booking platform
- answering questions about the owner's configured business

IMPORTANT:

The Django backend is responsible for deciding which information
is still missing and which actions should be performed.

You must NOT invent business information.

You should use the conversation context when answering.

Keep responses concise, natural and helpful.
"""


# =========================================================
# MESSAGE NORMALIZATION
# =========================================================

def normalize_messages(messages):
    """
    Convert BookForge/Gemini-style conversation messages
    into OpenAI-compatible chat messages.
    """

    normalized = []

    for message in messages:

        role = message.get("role", "user")

        if role == "model":
            role = "assistant"

        content = message.get("content")

        if content is None:

            parts = message.get("parts", [])

            text_parts = []

            for part in parts:

                if isinstance(part, dict):
                    text = part.get("text")

                    if text:
                        text_parts.append(text)

            content = "\n".join(text_parts)

        if not content:
            continue

        normalized.append(
            {
                "role": role,
                "content": str(content),
            }
        )

    return normalized


# =========================================================
# GROQ CHAT
# =========================================================

def groq_generate(messages):

    if not groq_client:
        raise RuntimeError("Groq API key is not configured.")

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=(
            [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            ]
            + normalize_messages(messages)
        ),
        temperature=0.2,
        max_tokens=1000,
    )

    return response.choices[0].message.content


# =========================================================
# OPENROUTER CHAT
# =========================================================

def openrouter_generate(messages):

    if not openrouter_client:
        raise RuntimeError(
            "OpenRouter API key is not configured."
        )

    response = openrouter_client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=(
            [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                }
            ]
            + normalize_messages(messages)
        ),
        temperature=0.2,
        max_tokens=1000,
    )

    return response.choices[0].message.content


# =========================================================
# GEMINI CHAT
# =========================================================

def gemini_generate(messages):

    if not gemini_client:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    gemini_messages = []

    for message in messages:

        role = message.get("role", "user")

        if role == "assistant":
            role = "model"

        content = message.get("content")

        if content is None:

            parts = message.get("parts", [])

            text_parts = []

            for part in parts:

                if isinstance(part, dict):

                    text = part.get("text")

                    if text:
                        text_parts.append(text)

            content = "\n".join(text_parts)

        if not content:
            continue

        gemini_messages.append(
            types.Content(
                role=role,
                parts=[
                    types.Part(
                        text=str(content)
                    )
                ],
            )
        )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=gemini_messages,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.2,
        ),
    )

    return response.text


# =========================================================
# JSON / TIME / DAY / EXTRACTION HELPERS
# =========================================================

def parse_json_response(raw):
    """
    Parse and normalize a provider JSON blob into a dictionary that
    the Pydantic BusinessInfo model can validate.
    """
    if isinstance(raw, dict):
        return raw

    if isinstance(raw, (str, bytes)):
        text = raw.strip() if isinstance(raw, str) else raw.decode("utf-8")
        if not text:
            return {}
        if text.startswith("```"):
            text = re.sub(r"```(?:json)?", "", text).strip()

        try:
            return json.loads(text)
        except Exception:
            try:
                # Some providers wrap JSON in a descriptive envelope.
                return json.loads(text.split("{", 1)[1].rsplit("}", 1)[0])
            except Exception:
                return {}

    return {}


DAY_MAP = {
    "monday": "Monday",
    "tuesday": "Tuesday",
    "wednesday": "Wednesday",
    "thursday": "Thursday",
    "friday": "Friday",
    "saturday": "Saturday",
    "sunday": "Sunday",
}


def normalize_day_name(value):
    key = str(value).strip().lower()
    return DAY_MAP.get(key, str(value).strip().title())


def normalize_time_text(value):
    """Convert explicit natural-language time expressions to HH:MM."""
    if not value:
        return None
    text = str(value).strip().lower().replace('.', '').replace(';', '')
    number_words = {
        "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
        "eleven": "11", "twelve": "12",
    }
    text = re.sub(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\b", lambda match: number_words[match.group(1)], text)
    if re.search(r"\b(?:noon|midday)\b", text):
        return "12:00"
    if re.search(r"\bmidnight\b", text):
        return "00:00"
    match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\b", text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    if hour > 23 or minute > 59:
        return None
    meridiem = re.search(r"\b(am|pm)\b", text)
    if meridiem:
        if not 1 <= hour <= 12:
            return None
        if meridiem.group(1) == "am":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12
    elif re.search(r"\b(?:morning)\b", text):
        hour = 0 if hour == 12 else hour
    elif re.search(r"\b(?:afternoon|evening|night)\b", text):
        hour = 12 if hour == 12 else hour + 12
    elif hour <= 12 and not re.fullmatch(r"\s*\d{1,2}:\d{2}\s*", text):
        # A bare 10 or 10:00 may mean either morning or evening.
        return None
    return f"{hour:02d}:{minute:02d}"


def extract_time_range(text):
    """Return normalized hours; incomplete or ambiguous meridiems stay unset."""
    if not text:
        return (None, None)
    token = r"(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)(?::\d{2})?(?:\s*(?:a\.?m\.?|p\.?m\.?|in the morning|in the afternoon|in the evening|at night))?"
    match = re.search(rf"(?P<open>{token})\s*(?:to|until|through|[-\u2013])\s*(?P<close>{token})", str(text), flags=re.I)
    if match:
        opening = normalize_time_text(match.group("open"))
        closing = normalize_time_text(match.group("close"))
        if opening and closing:
            return opening, closing
    value = str(text)
    opening_match = re.search(rf"\b(?:open|opens|opening)\b(?:\s+at)?\s+(?P<time>{token})", value, flags=re.I)
    closing_match = re.search(rf"\b(?:close|closes|closing)\b(?:\s+at)?\s+(?P<time>{token})", value, flags=re.I)
    if opening_match and closing_match:
        opening = normalize_time_text(opening_match.group("time"))
        closing = normalize_time_text(closing_match.group("time"))
        if opening and closing:
            return opening, closing
    return (None, None)


def expand_working_days_from_text(text):
    """Expand weekly ranges and common open/closed-day phrases."""
    if not text:
        return []
    raw = str(text)
    lower = raw.lower()
    ordered = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    if re.search(r"\b(?:daily|every day|all week|7 days a week|open all week)\b", lower):
        excluded = set()
        exclusion = re.search(r"\b(?:except|excluding|closed|close|off)\b(.+)$", lower)
        if exclusion:
            excluded = set(re.findall(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", exclusion.group(1)))
        return [day for day in ordered if day.lower() not in excluded]
    closed = set(re.findall(r"\b(?:close|closed|off)\s+(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)s?\b", lower))
    if closed:
        return [day for day in ordered if day.lower() not in closed]
    range_match = re.search(r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b\s*(?:to|through|thru|-)\s*\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", lower, flags=re.I)
    if range_match:
        start = normalize_day_name(range_match.group(1))
        end = normalize_day_name(range_match.group(2))
        start_index, end_index = ordered.index(start), ordered.index(end)
        if end_index < start_index:
            end_index += len(ordered)
        return [ordered[index % len(ordered)] for index in range(start_index, end_index + 1)]
    return [day for day in ordered if re.search(rf"\b{day}\b", raw, flags=re.I)]

def normalize_business_type(value):
    """Normalize the stored business type for the project bookkeeping."""
    if not value:
        return ""

    text = str(value).strip().lower()
    mapping = {
        "football turf": "sports_turf",
        "sports turf": "sports_turf",
        "turf": "sports_turf",
        "football ground": "sports_turf",
        "football pitch": "sports_turf",
        "sports facility": "sports_turf",
        "football_pitch": "sports_turf",
        "beauty salon": "salon",
        "hair salon": "salon",
        "dental clinic": "clinic",
        "dentist": "clinic",
        "dental": "clinic",
        "cafe": "restaurant",
        "coffee shop": "restaurant",
    }

    return mapping.get(text, text)


def assert_fallback_business_info(text, expected_fields=None, business_type=""):
    """Extract explicit onboarding details without relying on exact keywords."""
    info = BusinessInfo()
    message = str(text or "").strip()
    lower = message.lower()
    expected_fields = list(expected_fields or [])

    category_patterns = (
        ("sports_turf", r"\b(?:football[ _]turf|sports[ _]turf|turf|football\s+ground|football\s+pitch|sports\s+facility)\b"),
        ("salon", r"\b(?:beauty\s+salon|hair\s+salon|salon)\b"),
        ("clinic", r"\b(?:dental\s+clinic|clinic|dentist|dental)\b"),
        ("restaurant", r"\b(?:restaurant|cafe|coffee\s+shop)\b"),
    )
    for category, pattern in category_patterns:
        if re.search(pattern, lower):
            info.business_type = category
            break
    known_type = business_type or info.business_type

    name_patterns = (
        r"\b(?:called|named|known as)\s+(.+?)(?=[.!?]|$)",
        r"\b(?:let's call it|call the business|our shop is|my shop is|our name is)\s+(.+?)(?=[.!?]|$)",
        r"\b(?:business name|name)\s*(?:is|:)?\s+(.+?)(?=[.!?]|$)",
        r"\b(?:I run|I own|my business is|our business is)\s+(.+?)(?=[.!?]|$)",
    )
    for pattern in name_patterns:
        match = re.search(pattern, message, flags=re.I)
        if not match:
            continue
        candidate = match.group(1).strip(" ,;:")
        candidate = re.split(r",\s*(?:a|an|we|our|and we|based|located)\b", candidate, maxsplit=1, flags=re.I)[0]
        candidate = re.split(r"\s+(?:located|based)\s+(?:in|at)\s+|\s+in\s+(?=[A-Z])", candidate, maxsplit=1, flags=re.I)[0]
        candidate = re.sub(r"^(?:a|an|the)\s+", "", candidate, flags=re.I)
        if info.business_type and candidate.casefold().endswith(" " + info.business_type.casefold()):
            candidate = candidate[:-(len(info.business_type) + 1)].strip()
        if candidate and not re.match(r"^(?:located|based|in|at)\b", candidate, flags=re.I) and len(candidate) <= 200 and candidate.casefold() not in {"a restaurant", "a salon", "a clinic", "a turf"}:
            info.business_name = candidate
            break
    if not info.business_name:
        direct = re.search(r"^\s*([A-Z][\w&'?.-]*(?:\s+[A-Z][\w&'?.-]*)*)\s+is\s+(?:a|an)\s+(?:restaurant|cafe|coffee shop|salon|clinic|turf)\b", message, flags=re.I)
        if direct:
            info.business_name = direct.group(1).strip()
    if not info.business_name and "business_name" in expected_fields and len(message) <= 100 and not re.search(r"[?!\n]", message):
        candidate = re.sub(r"^(?:it's|it is|we are|our name is)\s+", "", message.strip(), flags=re.I)
        candidate = re.split(r"\s+(?:in|at)\s+", candidate, maxsplit=1, flags=re.I)[0]
        candidate = re.sub(r"^(?:a|an|the)\s+", "", candidate, flags=re.I).strip(" ,.")
        if info.business_type and candidate.casefold().endswith(" " + info.business_type.casefold()):
            candidate = candidate[:-(len(info.business_type) + 1)].strip()
        non_name = r"\b(?:open|closed|daily|every day|services?|hours?|tables?|pitches?|rooms?|chairs?|am|pm|restaurant|cafe|salon|clinic|dentist|dental|business|we have|i have)\b"
        if candidate and not info.website_style and not re.search(non_name, candidate, flags=re.I) and not re.search(r"@|\d{7,}", candidate) and not extract_time_range(candidate)[0]:
            info.business_name = candidate

    location_patterns = (
        r"\b(?:located|based|situated)\s+(?:in|at)\s+([^.!?\n]+)",
        r"\b(?:location|address)\s*(?:is|:)?\s*([^.!?\n]+)",
        r"\b(?:restaurant|cafe|business|salon|clinic|turf)\s+(?:is\s+)?in\s+([^.!?\n]+)",
        r"\b(?:named|called)\s+.+?\s+in\s+([A-Z][A-Za-z'?-]*(?:\s+[A-Z][A-Za-z'?-]*)*)",
        r"\bin\s+([A-Z][A-Za-z'?-]*(?:\s+[A-Z][A-Za-z'?-]*)*)",
    )
    for index, pattern in enumerate(location_patterns):
        if index == 4 and not (
            {"business_name", "business_type"}.intersection(expected_fields)
            or re.search(r"^\s*(?:actually|we are|we're|it is|it's)\b", lower)
        ):
            continue
        match = re.search(pattern, message, flags=re.I)
        if match:
            location = re.split(r"\s+(?:not|but|and we|and our)\b|[,;]", match.group(1), maxsplit=1, flags=re.I)[0].strip(" .")
            if location and len(location) <= 300:
                info.location = location
                break

    # Select a supported visual style from the owner's language. Delegation is
    # explicitly marked so the final summary can label it as an AI suggestion.
    delegate = re.search(r"\b(?:you choose|choose for me|whatever you think|what(?:ever)? fits|your choice|up to you|surprise me|you decide|recommend one)\b", lower)
    style_patterns = (
        ("modern", r"\b(?:modern|minimal|minimalist|sleek)\b"),
        ("elegant", r"\b(?:elegant|luxurious|luxury|premium|sophisticated)\b"),
        ("warm", r"\b(?:warm|welcoming|cozy|cosy|inviting)\b"),
        ("nature", r"\b(?:natural|relaxed|organic|botanical)\b"),
        ("bold", r"\b(?:bold|energetic|vibrant|sporty)\b"),
        ("playful", r"\b(?:playful|fun|cartoon|cheerful)\b"),
        ("illustrated", r"\billustrated\b"),
        ("3d", r"\b3d\b|\bmotion\b"),
    )
    for style, pattern in style_patterns:
        if re.search(pattern, lower):
            info.website_style = style
            break
    if delegate:
        from .business_setup import BUSINESS_TYPE_MAPPING
        canonical_type = BUSINESS_TYPE_MAPPING.get(known_type, known_type)
        category_style = {
            "restaurant": "warm", "salon": "elegant", "clinic": "modern", "sports_turf": "bold",
        }
        info.website_style = category_style.get(canonical_type)
        info.website_style_suggested = True

    # Parse natural service phrasing, keeping duration and price attached to
    # each service when the owner provides a semicolon-separated list.
    service_match = re.search(
        r"\b(?:our\s+)?services?(?:\s+(?:are|include|includes|such as)\s*|:)\s*|"
        r"\b(?:we offer|we provide|we serve|offerings include)\s*",
        message,
        flags=re.I,
    )
    service_infos = []
    service_text = None
    if service_match:
        service_text = message[service_match.end():]
        service_text = re.split(
            r"[.!?\n]|\b(?:we require|we need|our phone|our email|contact us)\b",
            service_text,
            maxsplit=1,
            flags=re.I,
        )[0]
    elif (
        expected_fields
        and expected_fields[0] == "services"
        and "?" not in message
        and not extract_time_range(message)[0]
        and not re.search(r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:dining\s+|treatment\s+|consultation\s+|styling\s+)?(?:tables?|rooms?|chairs?|pitches?|courts?|slots?)\b", lower)
        and len(message) <= 300
    ):
        service_text = message.strip(" .")
    if service_text:
        service_text = re.sub(
            r"(\d+\s*[- ]?a\s*[- ]?side)\s+and\s+(\d+\s*[- ]?a\s*[- ]?side\s+football)",
            r"\1 football and \2",
            service_text,
            flags=re.I,
        )
        chunks = (
            re.split(r";", service_text)
            if ";" in service_text
            else re.split(r",|\band\b|\bplus\b", service_text, flags=re.I)
        )
        seen = set()
        for chunk in chunks:
            raw = re.sub(r"^\s*(?:and|plus)\s+", "", chunk.strip(), flags=re.I)
            duration_match = re.search(
                r"\b(\d+)\s*(?:minutes?|mins?)\b|\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\b",
                raw,
                flags=re.I,
            )
            duration = None
            if duration_match:
                duration = (
                    int(duration_match.group(1))
                    if duration_match.group(1)
                    else int(float(duration_match.group(2)) * 60)
                )

            price_match = re.search(
                r"(?:\u20b9|INR\s*|Rs\.?\s*)([\d,]+(?:\.\d{1,2})?)|"
                r"([\d,]+(?:\.\d{1,2})?)\s*(?:INR|rupees?)\b",
                raw,
                flags=re.I,
            )
            price = None
            if price_match:
                amount = price_match.group(1) or price_match.group(2)
                price = float(amount.replace(",", ""))

            name_part = raw
            if duration_match:
                name_part = name_part[:duration_match.start()]
            if price_match:
                name_part = name_part[:min(len(name_part), price_match.start())]
            name = re.sub(r"[,;:\s]+$", "", name_part).strip(" \t\"'().[]{}.-")
            name = re.sub(r"^(?:service|offering)\s*[:-]?\s*", "", name, flags=re.I)
            if name and name.casefold() not in seen:
                seen.add(name.casefold())
                service_infos.append(ServiceInfo(
                    name=name,
                    price=price,
                    duration_minutes=duration,
                ))

    if service_infos:
        info.services = service_infos

    # Time range.
    opening, closing = extract_time_range(message)
    if opening:
        info.opening_time = opening
    if closing:
        info.closing_time = closing

    # Working days.
    days = expand_working_days_from_text(message)
    if days:
        info.working_days = days

    # Number of resources, including common number words.
    resources = re.search(
        r"\b(?:(?:have|offer|offers|with|including)\s+)?"
        r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
        r"(?:(?:shared|bookable|football|indoor|outdoor|dining|treatment|consultation|styling|appointment)\s+){0,3}"
        r"(?:pitches?|resources?|courts?|tables?|chairs?|rooms?|slots?)\b",
        message,
        flags=re.I,
    )
    if resources and ("number_of_resources" in expected_fields or re.search(r"\b(?:have|offer|offers|with|including)\b", message, flags=re.I)):
        count = resources.group(1).lower()
        info.number_of_resources = int(count) if count.isdigit() else {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        }[count]

    email_match = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", message, flags=re.I)
    if email_match:
        info.contact_email = email_match.group(0).rstrip(".,;:")

    phone_match = re.search(
        r"\b(?:phone(?:\s+number)?|mobile(?:\s+number)?|contact(?:\s+number)?|my\s+(?:phone|number)|call\s+us\s+at|reach\s+(?:us|me)\s+(?:at|on))\s*(?:is|:)?\s*(\+?[\d][\d\s().-]{6,}\d)",
        message,
        flags=re.I,
    )
    if phone_match:
        info.contact_phone = re.sub(r"\s+", " ", phone_match.group(1)).strip(" .,;:")

    deposit_match = re.search(
        r"(?:\u20b9|INR\s*|Rs\.?\s*)([\d,]+(?:\.\d{1,2})?)\s*(?:refundable\s+)?(?:booking\s+)?deposit\b|"
        r"\bdeposit\s*(?:is|of|:)?\s*(?:\u20b9|INR\s*|Rs\.?\s*)?([\d,]+(?:\.\d{1,2})?)",
        message,
        flags=re.I,
    )
    if deposit_match:
        amount = deposit_match.group(1) or deposit_match.group(2)
        info.booking_deposit = float(amount.replace(",", ""))

    booking_length_match = re.search(
        r"\b(?:standard\s+)?(?:booking|appointment)\s+(?:length|duration)\s*(?:is|of|:)?\s*(\d+)\s*(?:minutes?|mins?)\b",
        message,
        flags=re.I,
    )
    if booking_length_match:
        info.booking_length_minutes = int(booking_length_match.group(1))

    return info


# =========================================================
# GENERAL AI RESPONSE WITH FALLBACK
# =========================================================

def generate_ai_response(messages):

    if not messages:
        raise RuntimeError("No valid user message")

    normalized = normalize_messages(messages)
    valid_user_message = any(
        item.get("role") == "user" and str(item.get("content", "")).strip()
        for item in normalized
    )

    if not valid_user_message:
        raise RuntimeError("No valid user message")

    providers = [
        ("Gemini", gemini_generate),
        ("Groq", groq_generate),
        ("OpenRouter", openrouter_generate),
    ]

    errors = []

    for provider_name, provider_function in providers:

        try:

            print(f"Trying {provider_name}...")

            response = provider_function(messages)

            if response:
                print(
                    f"{provider_name} succeeded."
                )

                return response

        except Exception as error:

            print(
                f"{provider_name} failed: {error}"
            )

            errors.append(
                f"{provider_name}: {error}"
            )

    return (
        "I'm having trouble connecting to the AI service "
        "right now. Please try again."
    )


# =========================================================
# BUSINESS EXTRACTION PROMPT
# =========================================================

BUSINESS_EXTRACTION_PROMPT = """
You are the structured information extraction engine
for BookForge AI.

Extract ONLY information explicitly provided by the
business owner.

NEVER invent values.

Return JSON matching the BusinessInfo schema.

Extract these fields when present:

business_name
business_type
services
booking_deposit
opening_time
closing_time
working_days
location
contact_phone
contact_email
booking_length_minutes
number_of_resources

Recognize natural phrasings such as "our services are" and semicolon-separated
service lists. Preserve each service name and its stated duration and price.
Capture explicitly supplied location, phone, email, and booking deposit too.

IMPORTANT TIME RULES:

If the owner says:

"6 AM to 11 PM"

return:

opening_time = "06:00"
closing_time = "23:00"

If the owner says:

"9 AM to 7 PM"

return:

opening_time = "09:00"
closing_time = "19:00"

NEVER put the entire time range into one field.

Convert times to 24-hour HH:MM format.

Examples:

"6 in the morning" -> "06:00"
"6:30 AM" -> "06:30"
"11 PM" -> "23:00"
"10:30 PM" -> "22:30"

WORKING DAYS:

"Monday to Saturday"
should become:

["Monday", "Tuesday", "Wednesday",
 "Thursday", "Friday", "Saturday"]

"Monday, Wednesday and Friday"
should become:

["Monday", "Wednesday", "Friday"]

SERVICES:

If the owner says:

"5-a-side football, 7-a-side football,
birthday matches and tournaments"

extract all of them as separate services.

Do not ask questions.

Do not generate conversational text.

Return ONLY structured JSON.

Business owner's message:

"""


# =========================================================
# EXTRACTION USING GROQ
# =========================================================

def extract_business_info_with_groq(text):

    if not groq_client:
        raise RuntimeError("Groq API key is not configured.")

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": BUSINESS_EXTRACTION_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0,
        max_tokens=1500,
        response_format={
            "type": "json_object"
        },
    )

    content = response.choices[0].message.content

    data = json.loads(content)

    return BusinessInfo.model_validate(data)


# =========================================================
# EXTRACTION USING OPENROUTER
# =========================================================

def extract_business_info_with_openrouter(text):

    if not openrouter_client:
        raise RuntimeError(
            "OpenRouter API key is not configured."
        )

    response = openrouter_client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "system",
                "content": BUSINESS_EXTRACTION_PROMPT,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0,
        max_tokens=1500,
        response_format={
            "type": "json_object"
        },
    )

    content = response.choices[0].message.content

    data = json.loads(content)

    return BusinessInfo.model_validate(data)


# =========================================================
# EXTRACTION USING GEMINI
# =========================================================

def extract_business_info_with_gemini(text):

    if not gemini_client:
        raise RuntimeError(
            "Gemini API key is not configured."
        )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=(
            BUSINESS_EXTRACTION_PROMPT
            + "\n\n"
            + text
        ),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BusinessInfo,
            temperature=0,
        ),
    )

    if response.parsed:

        return BusinessInfo.model_validate(
            response.parsed
        )

    data = json.loads(response.text)

    return BusinessInfo.model_validate(data)


# =========================================================
# BUSINESS EXTRACTION WITH FALLBACK
# =========================================================

def extract_business_info(text):

    providers = [
        (
            "Groq",
            extract_business_info_with_groq,
        ),
        (
            "Gemini",
            extract_business_info_with_gemini,
        ),
        (
            "OpenRouter",
            extract_business_info_with_openrouter,
        ),
    ]

    for provider_name, provider_function in providers:

        try:

            print(
                f"Trying {provider_name} "
                f"for business extraction..."
            )

            result = provider_function(text)

            print(
                f"{provider_name} extraction succeeded."
            )

            return result

        except Exception as error:

            print(
                f"{provider_name} extraction failed: "
                f"{error}"
            )

    return BusinessInfo()


# =========================================================
# BOOKING EXTRACTION
# =========================================================

def extract_booking_request(text):

    prompt = """
Extract booking information from the customer message.

Only extract information explicitly provided.

Do not invent information.

Return JSON matching BookingRequest.

Convert exact dates to YYYY-MM-DD when possible.

Convert explicit times to HH:MM 24-hour format.

If information is missing, return null.

Customer message:
"""

    providers = []

    if groq_client:
        providers.append(
            ("Groq", groq_client)
        )

    if openrouter_client:
        providers.append(
            ("OpenRouter", openrouter_client)
        )

    for provider_name, client in providers:

        try:

            response = client.chat.completions.create(
                model=(
                    GROQ_MODEL
                    if provider_name == "Groq"
                    else OPENROUTER_MODEL
                ),
                messages=[
                    {
                        "role": "system",
                        "content": prompt,
                    },
                    {
                        "role": "user",
                        "content": text,
                    },
                ],
                temperature=0,
                max_tokens=1000,
                response_format={
                    "type": "json_object"
                },
            )

            data = json.loads(
                response.choices[0]
                .message.content
            )

            return BookingRequest.model_validate(
                data
            )

        except Exception as error:

            print(
                f"{provider_name} booking extraction "
                f"failed: {error}"
            )

    return BookingRequest()
