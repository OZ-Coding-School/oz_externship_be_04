from django.urls import path

from apps.notification.views.notification_views import NotificationListAPIView

app_name = "notification"

urlpatterns = [
    path("", NotificationListAPIView.as_view(), name="notification-list"),
]
