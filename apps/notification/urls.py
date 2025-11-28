from django.urls import path

from apps.notification.views.spec import NotificationListSpec

urlpatterns = [
    path("spec", NotificationListSpec.as_view(), name="notification-spec"),
]
