from rest_framework.pagination import CursorPagination


class NotificationCursorPagination(CursorPagination):
    page_size = 10
    page_size_query_param = "page_size"
    cursor_query_param = "cursor"
    ordering = "-created_at"
