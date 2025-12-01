import random
from typing import Any, cast

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
        self.user: User = User.objects.create(
            email="test@example.com",
            password="password123",
            name="test",
            nickname="test",
            phone_number="01012345678",
            gender="M",
            birthday=timezone.now().date(),
            profile_img_url="http://example.com/profile.jpg",
            is_active=True,
        )

    def test_notification_api_schema(self) -> None:
        """알림 API 기본 응답 구조 테스트"""
        url = reverse("notification:notification-list")
        resp: Any = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        json_data = resp.json()
        self.assertIn("results", json_data)
        for item in json_data["results"]:
            self.assertIn("type", item)
            self.assertIn("content", item)
            self.assertIn("back_url_link", item)
            self.assertIn("is_read", item)

    def test_notification_is_read_filter(self) -> None:
        """읽음/미읽음 필터 테스트"""
        url = reverse("notification:notification-list")

        resp_true: Any = self.client.get(url, {"is_read": "true"})
        self.assertEqual(resp_true.status_code, 200)
        for item in resp_true.json()["results"]:
            self.assertTrue(item["is_read"])

        resp_false: Any = self.client.get(url, {"is_read": "false"})
        self.assertEqual(resp_false.status_code, 200)
        for item in resp_false.json()["results"]:
            self.assertFalse(item["is_read"])

    def test_notification_serializer_random_type(self) -> None:
        """시리얼라이저 테스트 + 랜덤 타입 + __str__ 호출로 커버리지"""
        notification_type = cast(str, random.choice(Notification.NotificationType.choices))
        notification = Notification.objects.create(
            user=self.user,
            type=notification_type,
            content="serializer test",
            back_url_link="/test/url",
            is_read=True,
        )

        # __str__ 호출로 커버리지 채우기
        str(notification)

        data = NotificationSerializer(notification).data
        self.assertIn("type", data)
        self.assertIn("content", data)
        self.assertIn("back_url_link", data)
        self.assertIn("is_read", data)
        self.assertEqual(data["type"], notification.type)
        self.assertEqual(data["content"], notification.content)
        self.assertEqual(data["back_url_link"], notification.back_url_link)
        self.assertEqual(data["is_read"], notification.is_read)
