from decimal import Decimal, InvalidOperation
import re

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema
from .models import (
    AIConversation,
    AIMessage,
    BusinessConfiguration,
)
from .services.configuration_validator import (
    validate_business_configuration,
)

from .serializers import AIChatSerializer

from .services.ai_provider import (
    extract_business_info,
    assert_fallback_business_info,
    normalize_time_text,
    extract_time_range,
)

from .services.business_config import (
    update_business_configuration,
)

from .services.business_setup import (
    create_business_from_configuration,
)

# Keep this for now only if you still want the
# customer-facing AI booking endpoint as a future feature.
from .services.booking_ai import process_booking_request
from .services.onboarding import (
    get_next_onboarding_topic,
    get_onboarding_placeholder,
    get_onboarding_question as render_onboarding_question,
    get_setup_summary,
    suggest_website_style,
)


def validate_preview_services(value):
    """Validate editable service rows submitted with setup confirmation."""
    if not isinstance(value, list) or not value:
        raise ValueError("Add at least one service before creating the business.")

    normalized = []
    names = set()
    for service in value:
        if not isinstance(service, dict):
            raise ValueError("Each service must include a name, duration, and price.")

        name = str(service.get("name", "")).strip()
        if not name or len(name) > 100:
            raise ValueError("Service names must be between 1 and 100 characters.")
        if name.casefold() in names:
            raise ValueError(f"The service '{name}' is listed more than once.")
        names.add(name.casefold())

        try:
            duration = int(service.get("duration_minutes"))
            price = Decimal(str(service.get("price", 0)))
        except (TypeError, ValueError, InvalidOperation):
            raise ValueError(f"Enter a valid duration and price for {name}.")
        if duration <= 0:
            raise ValueError(f"Duration for {name} must be greater than zero.")
        if not price.is_finite() or price < 0 or price > Decimal("99999999.99"):
            raise ValueError(f"Price for {name} must be between ₹0 and ₹99,999,999.99.")

        normalized.append({
            "name": name,
            "duration_minutes": duration,
            "price": float(price),
        })

    return normalized


def get_onboarding_question(configuration, missing_fields, variation=0):
    """Compatibility wrapper used by tests and the onboarding endpoint."""
    topic = get_next_onboarding_topic(configuration, missing_fields)
    if topic is None and missing_fields:
        topic = missing_fields[0]
    return render_onboarding_question(configuration, topic, variation) if topic else None

@extend_schema(
    request=AIChatSerializer,
)
class AIChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # -----------------------------
        # 1. Validate request
        # -----------------------------

        serializer = AIChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data["message"]

        conversation_id = serializer.validated_data.get(
            "conversation_id"
        )

        # -----------------------------
        # 2. Get or create conversation
        # -----------------------------

        if conversation_id:

            conversation = AIConversation.objects.filter(
                id=conversation_id,
                owner=request.user,
            ).first()

            if not conversation:
                return Response(
                    {
                        "error": "Conversation not found."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        else:

            conversation = AIConversation.objects.create(
                owner=request.user,
                title="New Business Setup",
            )

        # -----------------------------
        # 3. Save owner's message
        # -----------------------------

        AIMessage.objects.create(
            conversation=conversation,
            role="user",
            content=message,
        )

        # -----------------------------
        # 4. Build conversation history
        # -----------------------------

        messages = conversation.messages.order_by(
            "created_at"
        )

        conversation_history = []

        for msg in messages:

            role = (
                "user"
                if msg.role == "user"
                else "model"
            )

            conversation_history.append(
                {
                    "role": role,
                    "parts": [
                        {
                            "text": msg.content
                        }
                    ],
                }
            )

        # -----------------------------
        # 5. Extract and save configuration
        # -----------------------------

        existing_configuration = BusinessConfiguration.objects.filter(conversation=conversation).first()
        existing_validation = validate_business_configuration(existing_configuration) if existing_configuration else {
            "missing_fields": ["business_name", "business_type", "services", "opening_time", "closing_time", "working_days", "number_of_resources"]
        }
        expected_fields = existing_validation["missing_fields"]
        business_info = extract_business_info(message)
        fallback_expected_fields = expected_fields
        if business_info.services:
            fallback_expected_fields = [field for field in expected_fields if field != "services"]
        fallback_info = assert_fallback_business_info(
            message,
            expected_fields=fallback_expected_fields,
            business_type=existing_configuration.business_type if existing_configuration else "",
        )
        # Explicitly parsed values are authoritative for corrections. Empty
        # extraction values never clear previously collected information.
        for field_name in (
            "business_name", "business_type", "opening_time", "closing_time",
            "working_days", "number_of_resources", "location", "contact_phone",
            "contact_email", "booking_deposit", "booking_length_minutes", "website_style",
        ):
            fallback_value = getattr(fallback_info, field_name, None)
            if fallback_value not in (None, "", []):
                setattr(business_info, field_name, fallback_value)
        business_info.website_style_suggested = fallback_info.website_style_suggested
        for field_name in ("opening_time", "closing_time"):
            value = normalize_time_text(getattr(business_info, field_name, None))
            setattr(business_info, field_name, value)
        for field_name in (
            "location",
            "contact_phone",
            "contact_email",
            "booking_deposit",
            "booking_length_minutes",
        ):
            if getattr(business_info, field_name) in (None, ""):
                fallback_value = getattr(fallback_info, field_name)
                if fallback_value not in (None, ""):
                    setattr(business_info, field_name, fallback_value)
        if fallback_info.services:
            known_services = {
                service.name.strip().casefold(): service
                for service in business_info.services
                if service.name.strip()
            }
            for fallback_service in fallback_info.services:
                key = fallback_service.name.strip().casefold()
                existing_service = known_services.get(key)
                if existing_service is None:
                    business_info.services.append(fallback_service)
                    known_services[key] = fallback_service
                    continue
                if existing_service.price is None:
                    existing_service.price = fallback_service.price
                if existing_service.duration_minutes is None:
                    existing_service.duration_minutes = fallback_service.duration_minutes

        # -----------------------------
        # 8. Update configuration
        # -----------------------------

        configuration = update_business_configuration(
            conversation,
            business_info,
        )
        skip_contact = bool(re.search(r"\b(?:skip|none|no thanks|not now|no contact details)\b", message, flags=re.I))
        if configuration.contact_phone or configuration.contact_email or skip_contact:
            if not configuration.contact_details_reviewed:
                configuration.contact_details_reviewed = True
                configuration.save(update_fields=["contact_details_reviewed", "updated_at"])
        if configuration.website_style_suggested and configuration.business_type:
            suggested_style = suggest_website_style(configuration.business_type)
            if configuration.website_style != suggested_style:
                configuration.website_style = suggested_style
                configuration.save(update_fields=["website_style", "updated_at"])
        validation = validate_business_configuration(
            configuration
        )

        # -----------------------------
        # 6. Generate setup or assistant response
        # -----------------------------

        setup_missing_fields = list(validation["missing_fields"])
        ambiguous_hours = bool(
            re.search(r"\b\d{1,2}(?::\d{2})?\s*(?:to|until|[-–])\s*\d{1,2}(?::\d{2})?\b", message, flags=re.I)
            and not extract_time_range(message)[0]
        )
        if ambiguous_hours and "opening_time" not in setup_missing_fields:
            setup_missing_fields.insert(0, "opening_time")
        if not validation["missing_fields"] and not configuration.contact_details_reviewed:
            setup_missing_fields.append("contact_details")
        if not validation["missing_fields"] and not configuration.website_style:
            setup_missing_fields.append("website_style")
        next_topic = get_next_onboarding_topic(configuration, setup_missing_fields)
        setup_ready = not setup_missing_fields and not ambiguous_hours

        if setup_ready:
            ai_response = (
                "Here's what I've gathered. Please review the summary and preview below. "
                "You can correct any detail here before confirming:\n\n"
                f"{get_setup_summary(configuration)}\n\n"
                "Does everything look right? Confirm in the preview when you're ready to create the website."
            )
        elif ambiguous_hours:
            ai_response = "I can't tell whether those times are AM or PM. Could you clarify both opening and closing times?"
        else:
            variation = AIMessage.objects.filter(conversation=conversation, role="assistant").count()
            ai_response = render_onboarding_question(configuration, next_topic, variation)

        # -----------------------------
        # 7. Save AI response
        # -----------------------------

        AIMessage.objects.create(
            conversation=conversation,
            role="assistant",
            content=ai_response,
        )

        # -----------------------------
        # 8. Return response
        # -----------------------------

        return Response(
            {
                "conversation_id": conversation.id,

                "message": ai_response,

                "business_configuration": {
                    "business_name": (
                        configuration.business_name
                    ),

                    "business_type": (
                        configuration.business_type
                    ),

                    "website_style": configuration.website_style,
                    "website_style_suggested": configuration.website_style_suggested,

                    "services": (
                        configuration.services
                    ),

                    "booking_deposit": (
                        configuration.booking_deposit
                    ),

                    "opening_time": (
                        configuration.opening_time
                    ),

                    "closing_time": (
                        configuration.closing_time
                    ),

                    "working_days": (
                        configuration.working_days
                    ),

                    "location": (
                        configuration.location
                    ),

                    "contact_phone": (
                        configuration.contact_phone
                    ),

                    "contact_email": (
                        configuration.contact_email
                    ),

                    "booking_length_minutes": (
                        configuration.booking_length_minutes
                    ),

                    "is_complete": setup_ready,
                    "missing_fields": setup_missing_fields,
                    "number_of_resources": (
                        configuration.number_of_resources
                    ),
                    "configuration_status": {
                        "is_complete": setup_ready,
                        "missing_fields": setup_missing_fields,
                    },
                },
                "next_topic": next_topic,
                "input_placeholder": get_onboarding_placeholder(next_topic, configuration.business_type),
                "is_complete": setup_ready,
            },
            status=status.HTTP_200_OK,
        )


class AIConfirmSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # -----------------------------
        # 1. Get conversation ID
        # -----------------------------

        conversation_id = request.data.get(
            "conversation_id"
        )

        if not conversation_id:
            return Response(
                {
                    "error": (
                        "conversation_id is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 2. Get owner's conversation
        # -----------------------------

        conversation = AIConversation.objects.filter(
            id=conversation_id,
            owner=request.user,
        ).first()

        if not conversation:
            return Response(
                {
                    "error": "Conversation not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -----------------------------
        # 3. Get configuration
        # -----------------------------

        try:
            configuration = (
                conversation.configuration
            )

        except BusinessConfiguration.DoesNotExist:
            return Response(
                {
                    "error": (
                        "Business configuration "
                        "does not exist."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "services" in request.data:
            try:
                configuration.services = validate_preview_services(
                    request.data["services"]
                )
            except ValueError as error:
                return Response(
                    {"error": str(error)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            configuration.save(update_fields=["services", "updated_at"])

        # -----------------------------
        # 4. Validate required information
        # -----------------------------

        validation = validate_business_configuration(configuration)
        if not validation["is_complete"]:

            return Response(
                {
                    "error": "Business setup is incomplete.",
                    "missing_fields": (
                        validation["missing_fields"]
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not configuration.opening_time:
            return Response(
                {
                    "error": (
                        "Opening time is missing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not configuration.closing_time:
            return Response(
                {
                    "error": (
                        "Closing time is missing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not configuration.working_days:
            return Response(
                {
                    "error": (
                        "Working days are missing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not configuration.number_of_resources:
            return Response(
                {
                    "error": (
                        "Number of resources "
                        "is missing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 5. Create actual platform
        # -----------------------------

        try:
            tenant = create_business_from_configuration(
                configuration,
                request.user,
                configuration.services,
                request.data.get("website_style") or configuration.website_style or "auto",
                request.data.get("website_font", "classic"),
                request.data.get("business_name_font", "editorial"),
                request.data.get("website_template", "auto"),
            )

        except ValueError as e:
            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 6. Mark configuration complete
        # -----------------------------

        configuration.is_complete = True

        configuration.save(
            update_fields=[
                "is_complete",
                "updated_at",
            ]
        )

        # -----------------------------
        # 7. Return result
        # -----------------------------

        return Response(
            {
                "message": (
                    "Business setup completed "
                    "successfully."
                ),
                "tenant_id": tenant.id,
                "business_id": tenant.id,
                "business_name": tenant.business_name,
                "slug": tenant.slug,
                "website_style": tenant.website_style,
                "website_font": tenant.website_font,
                "business_name_font": tenant.business_name_font,
                "website_template": tenant.website_template,
                "public_url": f"/book/{tenant.slug}",
            },
            status=status.HTTP_201_CREATED,
        )
# --------------------------------------------------
# FUTURE CUSTOMER AI BOOKING ENDPOINT
# --------------------------------------------------

class AIBookingView(APIView):

    def post(self, request):

        message = request.data.get("message")

        if not message:

            return Response(
                {
                    "error": "Message is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            result = process_booking_request(
                message
            )

            if not result["success"]:

                return Response(
                    result,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                result,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:

            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class AIConfirmSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # -----------------------------
        # 1. Get conversation ID
        # -----------------------------

        conversation_id = request.data.get(
            "conversation_id"
        )

        if not conversation_id:
            return Response(
                {
                    "error": (
                        "conversation_id is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 2. Get owner's conversation
        # -----------------------------

        conversation = AIConversation.objects.filter(
            id=conversation_id,
            owner=request.user,
        ).first()

        if not conversation:
            return Response(
                {
                    "error": "Conversation not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # -----------------------------
        # 3. Get configuration
        # -----------------------------

        try:
            configuration = (
                conversation.configuration
            )

        except BusinessConfiguration.DoesNotExist:
            return Response(
                {
                    "error": (
                        "Business configuration "
                        "does not exist."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "services" in request.data:
            try:
                configuration.services = validate_preview_services(
                    request.data["services"]
                )
            except ValueError as error:
                return Response(
                    {"error": str(error)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            configuration.save(update_fields=["services", "updated_at"])

        # -----------------------------
        # 4. Validate required information
        # -----------------------------

        validation = validate_business_configuration(configuration)
        if not validation["is_complete"]:

            return Response(
                {
                    "error": "Business setup is incomplete.",
                    "missing_fields": (
                        validation["missing_fields"]
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not configuration.opening_time:
            return Response(
                {
                    "error": (
                        "Opening time is missing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not configuration.closing_time:
            return Response(
                {
                    "error": (
                        "Closing time is missing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not configuration.working_days:
            return Response(
                {
                    "error": (
                        "Working days are missing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not configuration.number_of_resources:
            return Response(
                {
                    "error": (
                        "Number of resources "
                        "is missing."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 5. Create actual platform
        # -----------------------------

        try:
            tenant = create_business_from_configuration(
                configuration,
                request.user,
                configuration.services,
                request.data.get("website_style") or configuration.website_style or "auto",
                request.data.get("website_font", "classic"),
                request.data.get("business_name_font", "editorial"),
                request.data.get("website_template", "auto"),
            )

        except ValueError as e:
            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # -----------------------------
        # 6. Mark configuration complete
        # -----------------------------

        configuration.is_complete = True

        configuration.save(
            update_fields=[
                "is_complete",
                "updated_at",
            ]
        )

        # -----------------------------
        # 7. Return result
        # -----------------------------

        return Response(
            {
                "message": (
                    "Business setup completed "
                    "successfully."
                ),
                "tenant_id": tenant.id,
                "business_id": tenant.id,
                "business_name": tenant.business_name,
                "slug": tenant.slug,
                "website_style": tenant.website_style,
                "website_font": tenant.website_font,
                "business_name_font": tenant.business_name_font,
                "website_template": tenant.website_template,
                "public_url": f"/book/{tenant.slug}",
            },
            status=status.HTTP_201_CREATED,
        )
# --------------------------------------------------
# FUTURE CUSTOMER AI BOOKING ENDPOINT
# --------------------------------------------------

class AIBookingView(APIView):

    def post(self, request):

        message = request.data.get("message")

        if not message:

            return Response(
                {
                    "error": "Message is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            result = process_booking_request(
                message
            )

            if not result["success"]:

                return Response(
                    result,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                result,
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:

            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
