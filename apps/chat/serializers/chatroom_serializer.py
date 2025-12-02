from typing import Any, Dict, Optional

from rest_framework import serializers

from apps.chat.models import ChatMessage, LastReadMessage
from apps.study_groups.models import StudyGroup

from .message_serializer import SenderSerializer


class LastMessageSummarySerializer(serializers.ModelSerializer[ChatMessage]):
    sender = SenderSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ("id", "sender", "content", "created_at")


class ChatroomSerializer(serializers.ModelSerializer[StudyGroup]):
    # study group 채팅방
    last_message = serializers.SerializerMethodField()
    unread_message = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroup
        fields = (
            "id",
            "name",
            "profile_img_url",
            "start_at",
            "end_at",
            "last_message",
            "unread_message",
            "created_at",
            "updated_at",
        )

    def get_last_message(self, obj: StudyGroup) -> Optional[Dict[str, Any]]:
        last: Optional[ChatMessage] = obj.chat_messages.order_by("-created_at").select_related("sender").first()
        if not last:
            return None

        return LastMessageSummarySerializer(last, context=self.context).data

    def get_unread_count(self, obj: StudyGroup) -> Optional[int]:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        user = request.user

        # 읽은 마지막 메시지 timestamp

        last_read: Optional[LastReadMessage] = (
            LastReadMessage.objects.filter(study_group=obj, user=user).select_related("message").first()
        )
        if not last_read or not getattr(last_read, "message", None):
            count = obj.chat_messages.count()
            return count if count > 0 else None

        count = obj.chat_messages.filter(created_at__gt=last_read.message.created_at).count()
        return count if count > 0 else None
