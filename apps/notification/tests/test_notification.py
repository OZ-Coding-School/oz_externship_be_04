from typing import Any

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.notification.models import Notification
from apps.notification.serializers.notification_serializers import (
    NotificationSerializer,
)
from apps.users.models import User


class NotificationSchemaTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()

    def test_notification(self) -> None:
        url = reverse("notification:notification-list")
        resp: Any = self.client.get(url)
        self.assertEqual(resp.resolver_match.view_name, "notification:notification-list")
        self.assertEqual(resp.status_code, 200)

        json_data = resp.json()
        if json_data["results"]:
            first_item = json_data["results"][0]
            self.assertIn("type", first_item)
            self.assertIn("content", first_item)
            self.assertIn("back_url_link", first_item)

    def test_notification_is_read_filters(self) -> None:
        url = reverse("notification:notification-list")

        resp_true: Any = self.client.get(url, {"is_read": "true"})
        self.assertEqual(resp_true.status_code, 200)
        json_true = resp_true.json()
        for item in json_true["results"]:
            self.assertTrue(item["is_read"])

        resp_false: Any = self.client.get(url, {"is_read": "false"})
        self.assertEqual(resp_false.status_code, 200)
        json_false = resp_false.json()
        for item in json_false["results"]:
            self.assertFalse(item["is_read"])


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

        self.assertIn("type", data)
        self.assertIn("content", data)
        self.assertIn("back_url_link", data)
        self.assertEqual(data["type"], notification.type)
        self.assertEqual(data["content"], notification.content)
        self.assertEqual(data["back_url_link"], notification.back_url_link)
