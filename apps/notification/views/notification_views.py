from typing import Any, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notification.models import Notification
from apps.notification.pagination import NotificationCursorPagination
from apps.notification.serializers.notification_serializers import (
    NotificationSerializer,
)

User = get_user_model()
UserType = AbstractUser


class NotificationListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = NotificationCursorPagination

    @extend_schema(
        tags=["Notification"],
        summary="알림 목록 조회 API (읽음 여부 필터링 가능)",
        parameters=[
            OpenApiParameter(
                name="is_read",
                location="query",
                type=OpenApiTypes.BOOL,
                description="읽음 여부 필터링 쿼리 파라미터 입니다.",
            ),
            OpenApiParameter(
                name="page_size",
                location="query",
                type=OpenApiTypes.INT,
                description="각 페이지의 항목 수를 나타내는 쿼리 파라미터 입니다.",
            ),
            OpenApiParameter(
                name="cursor",
                location="query",
                type=OpenApiTypes.STR,
                description="커서 기반 페이지를 조회할 수 있는 쿼리 파라미터 입니다.",
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        is_read_param = request.query_params.get("is_read")  # true, false
        authenticated_user = cast(UserType, request.user)
        qs = Notification.objects.filter(user_id=authenticated_user.id)  # type: ignore

        if is_read_param is not None:
            if is_read_param.lower() == "true":
                qs = qs.filter(is_read=True)
            elif is_read_param.lower() == "false":
                qs = qs.filter(is_read=False)

        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(qs, request)

        # 시리얼라이즈
        serializer = self.serializer_class(paginated_qs, many=True)
        data: Any = serializer.data
        return paginator.get_paginated_response(data)
