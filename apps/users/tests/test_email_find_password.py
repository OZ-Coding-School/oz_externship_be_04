from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class FindPasswordEmailTestCase(APITestCase):

    def setUp(self) -> None:
        self.client = APIClient()
        self.send_url = reverse("find-password-send-email")
        self.verify_url = reverse("find-password-verify-email")
        self.email = "test@example.com"

        self.user = User.objects.create_user(
            email=self.email,
            password="test1234",
            name="홍길동",
            nickname="테스터",
            phone_number="01012345678",
            gender="M",
        )

    def tearDown(self) -> None:
        cache.clear()
        User.objects.all().delete()

    @patch("apps.users.utils.send_email.send_mail")
    def test_send_email_success(self, mock_send_mail: Any) -> None:
        response = self.client.post(self.send_url, {"email": self.email})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertIn("비밀번호 찾기", response.data["detail"])

        redis_key = f"email:find_password:{self.email}"
        self.assertIsNotNone(cache.get(redis_key))

    def test_send_email_invalid_format(self) -> None:
        response = self.client.post(self.send_url, {"email": "not-an-email"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_send_email_required(self) -> None:
        response = self.client.post(self.send_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    @patch("apps.users.utils.send_email.send_mail")
    def test_send_email_user_not_exists(self, mock_send_mail: Any) -> None:
        response = self.client.post(self.send_url, {"email": "notexist@example.com"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_email_success(self) -> None:
        code = "123456"
        cache.set(f"email:find_password:{self.email}", code, timeout=300)

        response = self.client.post(self.verify_url, {"email": self.email, "code": code})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertIn("비밀번호 찾기", response.data["detail"])

        self.assertEqual(cache.get(f"email_verified:find_password:{self.email}"), True)

    def test_verify_email_wrong_code(self) -> None:
        cache.set(f"email:find_password:{self.email}", "123456", timeout=300)

        response = self.client.post(self.verify_url, {"email": self.email, "code": "000000"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_verify_email_expired(self) -> None:
        response = self.client.post(self.verify_url, {"email": self.email, "code": "123456"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_verify_email_invalid_email_format(self) -> None:
        response = self.client.post(self.verify_url, {"email": "not-an-email", "code": "123456"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_verify_email_code_not_digit(self) -> None:
        response = self.client.post(self.verify_url, {"email": self.email, "code": "abcdef"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_verify_email_required_email(self) -> None:
        response = self.client.post(self.verify_url, {"code": "123456"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("email", response.data["error_detail"])

    def test_verify_email_required_code(self) -> None:
        response = self.client.post(self.verify_url, {"email": self.email})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("code", response.data["error_detail"])
