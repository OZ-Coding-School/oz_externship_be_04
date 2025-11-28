from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notification.models import Notification
from apps.notification.pagination import NotificationCursorPagination
from apps.notification.serializers.notification_serializers import (
    NotificationSerializer,
)
from apps.users.models import User


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Notification"],
        summary="전체 알림을 조회할 수 있는 API입니다.",
        responses={
            200: NotificationSerializer(many=True),
            401: {
                "type": "object",
                "properties": {"detail": {"type": "string"}},
                "example": {"detail": "자격 인증 데이터가 제공되지 않았습니다."},
            },
            500: {
                "type": "object",
                "properties": {"detail": {"type": "string"}},
                "example": {"detail": "인터넷 서버 에러"},
            },
        },
    )
    def get(self, request: Request) -> Response:
        user = cast(User, request.user)
        qs = Notification.objects.filter(user=user)

        # CursorPagination
        paginator = NotificationCursorPagination()
        paginator_qs = paginator.paginate_queryset(qs, request)

        serializer = NotificationSerializer(paginator_qs, many=True)
        return paginator.get_paginated_response(serializer.data)
