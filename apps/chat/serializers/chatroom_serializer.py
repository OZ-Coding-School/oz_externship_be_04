from typing import Any

from rest_framework import serializers


class SenderMiniSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField(read_only=True)
    nickname = serializers.CharField(read_only=True)


class LastMessageSummarySerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField(read_only=True)
    sender = SenderMiniSerializer(read_only=True)
    content = serializers.CharField(read_only=True)
    is_read = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class ChatroomSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    unread_message = serializers.IntegerField(read_only=True)
    last_message = LastMessageSummarySerializer(read_only=True, allow_null=True)
