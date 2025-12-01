import random
from base64 import b64decode
from typing import Any, Optional, cast
from urllib import parse
from urllib.parse import unquote

from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound
from rest_framework.pagination import Cursor, CursorPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notification.models import Notification
from apps.notification.serializers.notification_serializers import (
    NotificationSerializer,
)


class MockCursorPagination(CursorPagination):
    """
    목 데이터용 CursorPagination 구현체
    """

    page_size_query_param = "page_size"
    page_size = 10
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=...) -> Optional[list[Any]]:  # type: ignore
        self.request = request
        self.page_size = cast(int, self.get_page_size(request))
        if not self.page_size:
            return None

        self.base_url = request.build_absolute_uri()
        self.ordering = ["id"]
        self.cursor = self.decode_cursor(request)
        if self.cursor is None:
            (offset, reverse, current_position) = (0, False, None)
        else:
            (offset, reverse, current_position) = self.cursor

        # Cursor pagination always enforces an ordering.
        if reverse:
            queryset = reversed(queryset)
        else:
            queryset = queryset

        # If we have a cursor with a fixed position then filter by that.
        if current_position is not None:
            order = self.ordering[0]
            is_reversed = order.startswith("-")
            order_attr = order.lstrip("-")

            filtered = []
            for q in queryset:
                ordering_attr = getattr(q, order_attr, None)
                if ordering_attr is not None:
                    if self.cursor.reverse != is_reversed:  # type: ignore
                        if ordering_attr < int(current_position):
                            filtered.append(q)
                    else:
                        if ordering_attr > int(current_position):
                            filtered.append(q)

            queryset = filtered

        # If we have an offset cursor then offset the entire page by that amount.
        # We also always fetch an extra item in order to determine if there is a
        # page following on from this one.
        results = list(queryset[offset : offset + self.page_size + 1])
        self.page = list(results[: self.page_size])

        # Determine the position of the final item following the page.
        if len(results) > len(self.page):
            has_following_position = True
            following_position = self._get_position_from_instance(results[-1], self.ordering)
        else:
            has_following_position = False
            following_position = None

        if reverse:
            # If we have a reverse queryset, then the query ordering was in reverse
            # so we need to reverse the items again before returning them to the user.
            self.page = list(reversed(self.page))

            # Determine next and previous positions for reverse cursors.
            self.has_next = (current_position is not None) or (offset > 0)
            self.has_previous = has_following_position
            if self.has_next:
                self.next_position = current_position  # type: ignore
            if self.has_previous:
                self.previous_position = following_position
        else:
            # Determine next and previous positions for forward cursors.
            self.has_next = has_following_position
            self.has_previous = (current_position is not None) or (offset > 0)
            if self.has_next:
                self.next_position = following_position
            if self.has_previous:
                self.previous_position = current_position  # type: ignore

        # Display page controls in the browsable API if there is more
        # than one page.
        if (self.has_previous or self.has_next) and self.template is not None:
            self.display_page_controls = True

        return self.page

    def decode_cursor(self, request: Request) -> Optional[Cursor]:
        """
        Given a request with a cursor, return a `Cursor` instance.
        """
        encoded = request.query_params.get(self.cursor_query_param)
        if encoded is None:
            return None

        encoded = unquote(encoded)

        def _positive_int(integer_string, strict=False, cutoff=None):  # type: ignore
            """
            Cast a string to a strictly positive integer.
            """
            ret = int(integer_string)
            if ret < 0 or (ret == 0 and strict):
                raise ValueError()
            if cutoff:
                return min(ret, cutoff)
            return ret

        try:
            querystring = b64decode(encoded.encode("ascii")).decode("ascii")
            tokens = parse.parse_qs(querystring, keep_blank_values=True)

            offset = tokens.get("o", ["0"])[0]
            offset = _positive_int(offset, cutoff=self.offset_cutoff)  # type: ignore

            reverse = tokens.get("r", ["0"])[0]
            reverse = bool(int(reverse))  # type: ignore

            position = tokens.get("p", [None])[0]
        except (TypeError, ValueError) as e:
            raise NotFound(self.invalid_cursor_message)

        return Cursor(offset=offset, reverse=reverse, position=position)  # type: ignore


# 모킹
class NotificationListAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = NotificationSerializer

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
                description="페이지 네이션 적용 시 각 페이지의 항목 수를 나타내는 쿼리 파라미터 입니다.",
            ),
            OpenApiParameter(
                name="cursor",
                location="query",
                type=OpenApiTypes.STR,
                description="특정 커서 위치에 해당하는 페이지를 조회할 수 있는 쿼리 파라미터 입니다.",
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        is_read_param = request.query_params.get("is_read")  # true, false
        qs = [
            Notification(
                id=i,
                type=cast(str, random.choice(Notification.NotificationType.choices)),
                content=f"test notification {i}",
                back_url_link=f"https://example.com/{i}",
                is_read=random.choice([True, False]),
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            for i in range(1, 50)
        ]

        if is_read_param:
            if is_read_param.lower() == "true":
                qs = [notification for notification in qs if notification.is_read]
            elif is_read_param.lower() == "false":
                qs = [notification for notification in qs if not notification.is_read]

        paginator = MockCursorPagination()
        paginated_qs = paginator.paginate_queryset(qs, request)

        # 시리얼라이즈
        serializer = NotificationSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)
