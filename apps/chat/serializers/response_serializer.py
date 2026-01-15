from typing import Any

from rest_framework import serializers


class ErrorResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()


class MarkAllReadResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()
