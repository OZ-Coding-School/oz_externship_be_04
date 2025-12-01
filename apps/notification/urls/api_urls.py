from django.urls import path

from apps.notification.views.read_views import (
    NotificationReadAllViews,
    NotificationReadView,
)

app_name = "notification"

urlpatterns = [
    path("<int:notification_id>/read", NotificationReadView.as_view(), name="notification-read"),
    path("read-all", NotificationReadAllViews.as_view(), name="notification-read-all"),
]
