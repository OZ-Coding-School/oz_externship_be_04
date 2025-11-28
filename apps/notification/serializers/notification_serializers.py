from rest_framework import serializers

from apps.notification.models import Notification


# 일반적인 필드는 읽기 전용으로 두어 일방향으로 보게 되는 알림의 특성상 읽기만 가능한 시리얼라이저
class NotificationSerializer(serializers.ModelSerializer["Notification"]):
    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "content",
            "is_read",
            "created_at",
            "back_url_link",
        ]
        read_only_fields = fields


# is_read 시리얼라이저를 통해 유저가 "읽음"에 대해서는 post로 변경할 수 있도록 해줌
class NotificationReadSerializer(serializers.ModelSerializer["Notification"]):
    class Meta:
        model = Notification
        fields = ["is_read"]

    # is_read False -> True만 가능 하도록
    def validate_is_read(self, value: bool) -> bool:
        if value is not True:
            raise serializers.ValidationError("is_read는 True만 가능합니다.")
        return value