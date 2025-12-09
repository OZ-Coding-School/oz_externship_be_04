from django.urls import path

from apps.notification.views.notification_views import NotificationListAPIView
from apps.notification.views.read_views import (
    NotificationReadAllView,
    NotificationReadView,
)
from apps.notification.views.sse_views import notification_stream

app_name = "notification"

urlpatterns = [
    path("", NotificationListAPIView.as_view(), name="notification-list"),
    path("stream", notification_stream, name="notification-stream"),
    path("<int:notification_id>/read", NotificationReadView.as_view(), name="notification-read"),
    path("read-all", NotificationReadAllView.as_view(), name="notification-read-all"),
]
