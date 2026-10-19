from rest_framework import serializers


class AIChatSerializer(serializers.Serializer):
    message = serializers.CharField(
        trim_whitespace=True,
        allow_blank=False,
    )
    conversation_id = serializers.IntegerField(
        required=False,
        allow_null=True
    )