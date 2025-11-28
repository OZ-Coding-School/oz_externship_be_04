from django.urls import path

from apps.notification.views.views import NotificationListView

urlpatterns = [
    path("notifications", NotificationListView.as_view()),
]
