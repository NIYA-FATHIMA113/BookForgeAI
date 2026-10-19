from rest_framework import serializers

from .models import BusinessHours


class BusinessHoursSerializer(serializers.ModelSerializer):

    class Meta:
        model = BusinessHours

        fields = [
            "id",
            "day_of_week",
            "opening_time",
            "closing_time",
            "is_closed",
        ]

        read_only_fields = [
            "id",
        ]

    def validate(self, attrs):

        is_closed = attrs.get(
            "is_closed",
            getattr(self.instance, "is_closed", False)
        )

        opening_time = attrs.get(
            "opening_time",
            getattr(self.instance, "opening_time", None)
        )

        closing_time = attrs.get(
            "closing_time",
            getattr(self.instance, "closing_time", None)
        )

        if not is_closed:

            if opening_time is None or closing_time is None:
                raise serializers.ValidationError(
                    "Opening time and closing time are required."
                )

            if opening_time >= closing_time:
                raise serializers.ValidationError(
                    "Closing time must be after opening time."
                )

        return attrs