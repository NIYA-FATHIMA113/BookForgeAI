from django.conf import settings
from django.db import models


class AIConversation(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ai_conversations",
    )

    title = models.CharField(
        max_length=200,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.owner.username} - {self.title or 'AI Conversation'}"

class AIMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.role} - {self.conversation.id}"

class BusinessConfiguration(models.Model):
    conversation = models.OneToOneField(
        AIConversation,
        on_delete=models.CASCADE,
        related_name="configuration",
    )

    business_name = models.CharField(
        max_length=200,
        blank=True,
    )

    business_type = models.CharField(
        max_length=100,
        blank=True,
    )

    services = models.JSONField(
        default=list,
        blank=True,
    )

    booking_deposit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )

    opening_time = models.TimeField(
        null=True,
        blank=True,
    )

    closing_time = models.TimeField(
        null=True,
        blank=True,
    )

    working_days = models.JSONField(
        default=list,
        blank=True,
    )

    location = models.CharField(
        max_length=300,
        blank=True,
    )

    contact_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    contact_email = models.EmailField(
        blank=True,
    )

    booking_length_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    number_of_resources = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    is_complete = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )
    def check_completion(self):
        required_fields = [
            self.business_name,
            self.business_type,
            self.services,
            self.opening_time,
            self.closing_time,
            self.working_days,
            self.number_of_resources,
        ]

        return all(required_fields)

    def get_missing_fields(self):
        missing = []

        if not self.business_name:
            missing.append("business_name")

        if not self.business_type:
            missing.append("business_type")

        business_type = (
            self.business_type.strip().lower()
            if self.business_type
            else ""
        )

        # --------------------------------
        # Business-specific requirements
        # --------------------------------

        if business_type in ["salon", "clinic"]:
            if not self.services:
                missing.append("services")

            if not self.number_of_resources:
                missing.append("number_of_resources")

        elif business_type == "sports_turf":
            if not self.number_of_resources:
                missing.append("number_of_resources")

        elif business_type == "restaurant":
            # Restaurants use tables/seating as resources.
            # Services are NOT required.
            if not self.number_of_resources:
                missing.append("number_of_resources")

        else:
            # Unknown business type
            if not self.services:
                missing.append("services")

            if not self.number_of_resources:
                missing.append("number_of_resources")

        # --------------------------------
        # Common requirements
        # --------------------------------

        if not self.opening_time:
            missing.append("opening_time")

        if not self.closing_time:
            missing.append("closing_time")

        if not self.working_days:
            missing.append("working_days")

        return missing

    def check_completion(self):
        """
        Determine whether the business configuration contains
        the minimum information required for setup.
        """

        if not self.business_name:
            return False

        if not self.business_type:
            return False

        business_type = (
            self.business_type.lower().strip()
        )

        # Common requirements
        if not self.opening_time:
            return False

        if not self.closing_time:
            return False

        if not self.working_days:
            return False

        # Sports turf
        if business_type in [
            "football turf",
            "sports turf",
            "turf",
            "sports_turf",
        ]:

            if not self.number_of_resources:
                return False

            return True

        # Restaurant
        if business_type in [
            "restaurant",
            "cafe",
            "coffee shop",
        ]:

            return True

        # Salon / clinic / normal service businesses
        if not self.services:
            return False

        if not self.number_of_resources:
            return False

        return True


    def get_missing_fields(self):

        missing = []

        if not self.business_name:
            missing.append("business_name")

        if not self.business_type:
            missing.append("business_type")

        business_type = (
            self.business_type.lower().strip()
            if self.business_type
            else ""
        )

        if business_type in [
            "football turf",
            "sports turf",
            "turf",
            "sports_turf",
        ]:

            if not self.number_of_resources:
                missing.append(
                    "number_of_resources"
                )

        elif business_type in [
            "restaurant",
            "cafe",
            "coffee shop",
        ]:

            pass

        else:

            if not self.services:
                missing.append("services")

            if not self.number_of_resources:
                missing.append(
                    "number_of_resources"
                )

        if not self.opening_time:
            missing.append("opening_time")

        if not self.closing_time:
            missing.append("closing_time")

        if not self.working_days:
            missing.append("working_days")

        return missing
    def __str__(self):
        return self.business_name or "Business Configuration"