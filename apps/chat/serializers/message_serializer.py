from typing import Any, Optional, cast

from rest_framework import serializers
from rest_framework.request import Request

from apps.chat.models import ChatMessage, LastReadMessage
from apps.users.models import User
from config.settings.base import value


class SenderSerializer(serializers.ModelSerializer[User]):
    profile_img_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "nickname",
            "profile_img_url",
        )

    def get_profile_img_url(self, obj: User) -> Optional[str]:
        profile = getattr(obj, "profile", None)
        if profile:
            try:
                url = cast(str, profile.profile_img_url)
                return url
            except (ValueError, TypeError):
                return None
        return None


class MessageSerializer(serializers.ModelSerializer[ChatMessage]):
    sender = SenderSerializer(read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "sender",
            "content",
            "created_at",
            "is_read",
        )

    def get_is_read(self, obj: ChatMessage) -> bool:
        # request 가져오기
        request: Optional[Request] = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        user = request.user

        # 마지막 읽은 메시지 조회
        try:
            last_read = (
                LastReadMessage.objects.filter(study_group=obj.study_group, user=user).select_related("message").first()
            )
        except (ValueError, TypeError):
            return False

        if not last_read or not getattr(last_read, "message", None):
            return False

        return obj.created_at <= last_read.message.created_at


class MessageCreateRequestSerializer(serializers.Serializer[Any]):
    content = serializers.CharField(
        max_length=1000,  # 필요시 조정 가능함
        allow_blank=False,
        trim_whitespace=True,
    )

    def validate_content(self, value: Any) -> str:
        # 공백만 있는 문자 방지
        text = cast(str, value)

        if not text.strip():
            raise serializers.ValidationError("메시지 내용은 비어 있을 수 없습니다.")

        return text
