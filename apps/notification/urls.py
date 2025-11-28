from django.urls import path

from apps.notification.views.views import NotificationListView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
]
