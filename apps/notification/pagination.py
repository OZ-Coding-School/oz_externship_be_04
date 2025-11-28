from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class NotificationCursorPagination(CursorPagination):
    page_size = 10
    page_size_query_param = "page_size"
    cursor_query_param = "cursor"
    ordering = "-created_at"

    def get_paginated_response(self, data: Iterable[Any]) -> Response:
        next_cursor_value = None

        next_link = self.get_next_link()
        if next_link:
            parsed = urlparse(next_link)
            next_cursor_value = parse_qs(parsed.query).get("cursor", [None])[0]

        return Response({"results": data, "next_cursor": next_cursor_value})
