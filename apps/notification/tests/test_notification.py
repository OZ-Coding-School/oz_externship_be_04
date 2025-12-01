from typing import Any

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.notification.models import Notification
from apps.notification.serializers.notification_serializers import (
    NotificationSerializer,
)
from apps.users.models import User


class NotificationTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_notification(self) -> None:
        url = reverse("notification:notification-list")
        resp: Any = self.client.get(url)
        assert resp.resolver_match.view_name == "notification:notification-list"
        assert resp.status_code == 200


class NotificationSerializerTests(TestCase):
    def setUp(self) -> None:
        self.user: User = User.objects.create(
            email="test@example.com",
            password="password123",
            name="test",
            nickname="test",
            phone_number="01012345678",
            gender="M",
            birthday=timezone.now().date(),  # 오늘 날짜로 설정
            profile_img_url="http://example.com/profile.jpg",
            is_active=True,
        )

    def test_serializer_valid_data(self) -> None:
        notification: Notification = Notification.objects.create(
            user=self.user, content="test", type=Notification.NotificationType.STUDY_JOIN, back_url_link="/test/url"
        )
        data = NotificationSerializer(notification).data

        assert data["type"] == notification.type
