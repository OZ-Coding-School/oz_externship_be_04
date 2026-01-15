import random
from typing import Any

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notification.models import Notification
from apps.notification.serializers.notification_serializers import (
    NotificationSerializer,
)
from apps.users.models import User


class NotificationTests(TestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user: User = User.objects.create_user(
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
        # 👉 JWT 발급
        refresh = RefreshToken.for_user(self.user)
        access = str(refresh.access_token)

        # 👉 테스트 클라이언트에 Authorization 헤더 추가
        self.client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {access}"

        Notification.objects.create(
            user=self.user,
            type="TEST",
            content="base content",
            back_url_link="/base",
            is_read=False,
        )
        Notification.objects.create(
            user=self.user,
            type="TEST",
            content="read content",
            back_url_link="/read",
            is_read=True,
        )

    def test_notification_api_schema(self) -> None:
        """알림 API 기본 응답 구조 테스트"""
        url = reverse("notification:notification-list")
        resp: Any = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        json_data = resp.json()

        self.assertIn("next", json_data)
        self.assertIn("previous", json_data)
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

        true_results = resp_true.json()["results"]
        self.assertGreater(len(true_results), 0)

        for item in true_results:
            self.assertTrue(item["is_read"])

        resp_false: Any = self.client.get(url, {"is_read": "false"})
        self.assertEqual(resp_false.status_code, 200)

        false_results = resp_false.json()["results"]
        self.assertGreater(len(false_results), 0)
        for item in false_results:
            self.assertFalse(item["is_read"])

    def test_notification_serializer_random_type(self) -> None:
        """시리얼라이저 테스트 + 랜덤 타입 + __str__ 호출로 커버리지"""

        # choices = [("A", "알림A"), ("B", "알림B")] 형태이므로 첫 값만 사용
        type_choice = random.choice([c[0] for c in Notification.NotificationType.choices])

        notification = Notification.objects.create(
            user=self.user,
            type=type_choice,
            content="serializer test",
            back_url_link="/test/url",
            is_read=True,
        )

        # __str__ 호출로 커버리지 채우기
        str(notification)

        data = NotificationSerializer(notification).data
        # 필드 존재 여부 검증
        self.assertIn("type", data)
        self.assertIn("content", data)
        self.assertIn("back_url_link", data)
        self.assertIn("is_read", data)

        # 직렬화 값 비교
        self.assertEqual(data["type"], notification.type)
        self.assertEqual(data["content"], notification.content)
        self.assertEqual(data["back_url_link"], notification.back_url_link)
        self.assertEqual(data["is_read"], notification.is_read)
