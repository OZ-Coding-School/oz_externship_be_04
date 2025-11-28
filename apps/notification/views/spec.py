from datetime import datetime, timezone
from typing import Any, cast

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notification.models import Notification
from apps.notification.serializers.notification_serializers import (
    NotificationSerializer,
)
from apps.users.models import User


# 모킹
class NotificationListSpec(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = cast(User, request.user)

        # 모킹 데이터 생성
        notif = Notification(
            id=1,
            user=user,
            type=Notification.NotificationType.STUDY_NOTE_CREATE,
            content="파이썬 스터디에 새로운 노트가 기록되었습니다!",
            back_url_link="http://example.com/study/1/notes/1",
            is_read=False,
        )
        notif.created_at = datetime(2025, 11, 20, 0, 0, 5, tzinfo=timezone.utc)

        # 시리얼라이즈
        serializer = NotificationSerializer([notif], many=True)
        return Response(
            {
                "results": serializer.data,
                "next_cursor": "mocked_cursor_for_next_page",
            }
        )
