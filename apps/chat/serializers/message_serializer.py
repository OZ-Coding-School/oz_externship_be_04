from rest_framework import serializers

from apps.chat.models.chat_message import ChatMessage
from apps.users.models import User


class SenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "profile_img_url"
            ]

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "sender",
            "content",
            "created_at",
        ]
        read_only_fields = fields