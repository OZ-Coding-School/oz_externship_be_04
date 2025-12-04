from rest_framework import serializers


class MarkAllReadResponseSerializer(serializers.Serializer):  # type: ignore[type-arg]
    detail = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):  # type: ignore[type-arg]
    error_detail = serializers.CharField()
