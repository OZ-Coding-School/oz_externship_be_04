from django.urls import path

from apps.notification.views.notification_views import NotificationListAPIView
from apps.notification.views.read_views import (
    NotificationReadAllView,
    NotificationReadView,
)
from apps.notification.views.sse_views import notification_stream

app_name = "notification"

urlpatterns = [
    path("notification", NotificationListAPIView.as_view(), name="notification-list"),
    path("notification/stream", notification_stream, name="notification-stream"),
    path("notification/<int:notification_id>/read", NotificationReadView.as_view(), name="notification-read"),
    path("notification/read-all", NotificationReadAllView.as_view(), name="notification-read-all"),
]
