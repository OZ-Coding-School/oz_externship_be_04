from django.urls import path

from apps.notification.views.notification_views import NotificationListAPIView
from apps.notification.views.read_views import (
    NotificationReadAllView,
    NotificationReadView,
)

app_name = "notification"

urlpatterns = [
    path("", NotificationListAPIView.as_view(), name="notification-list"),
    path("<int:notification_id>/read", NotificationReadView.as_view(), name="notification-read"),
    path("read-all", NotificationReadAllView.as_view(), name="notification-read-all"),
]
