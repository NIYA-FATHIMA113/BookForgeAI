from rest_framework import serializers

from .models import Service, Resource


class ServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Service
        fields = [
            "id",
            "name",
            "duration",
            "price",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]


class ResourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Resource

        fields = [
            "id",
            "tenant",
            "name",
            "is_active",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "tenant",
            "created_at",
        ]
