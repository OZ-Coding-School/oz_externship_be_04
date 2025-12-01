from django.urls import path

from apps.notification.views.notification_views import NotificationListAPIView

urlpatterns = [
    path("", NotificationListAPIView.as_view(), name="notification-list"),
]
