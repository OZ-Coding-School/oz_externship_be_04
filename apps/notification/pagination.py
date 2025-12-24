from collections import OrderedDict
from typing import Any, Optional

from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class NotificationCursorPagination(CursorPagination):
    total_count: Optional[int] = None
    unread_total: Optional[int] = None
    page_size = 10
    page_size_query_param = "page_size"
    cursor_query_param = "cursor"
    ordering = "-created_at"

    # 알림 전체 개수 표기하기
    def get_paginated_response(self, data: Any) -> Response:
        return Response(
            OrderedDict(
                [
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("total", getattr(self, "total_count", None)),
                    ("unread_total", getattr(self, "unread_total", None)),
                    ("results", data),
                ]
            )
        )
