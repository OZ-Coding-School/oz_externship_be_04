from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
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

        mail.outbox = []
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

    @patch("apps.users.utils.send_auth.AuthCodeCache.generate_mail_code")
    def test_send_email_success(self, mock_generate: Any) -> None:
        mock_generate.return_value = "asd123"
        response = self.client.post(self.send_url, {"email": self.email})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertIn("비밀번호 찾기", response.data["detail"])

        redis_key = f"email:reset_password:{self.email}"
        stored_code = cache.get(redis_key)
        self.assertIsNotNone(stored_code)
        self.assertEqual(stored_code, "asd123")

    def test_send_email_invalid_format(self) -> None:
        response = self.client.post(self.send_url, {"email": "not-an-email"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_send_email_required(self) -> None:
        response = self.client.post(self.send_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    @patch("apps.users.utils.send_auth.AuthCodeCache.generate_mail_code")
    def test_send_email_user_not_exists(self, mock_generate: Any) -> None:
        mock_generate.return_value = "asd123"
        response = self.client.post(self.send_url, {"email": "notexist@example.com"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_email_success(self) -> None:
        code = "asA456"
        email = self.email

        cache_key = f"email:reset_password:{email}"
        cache.set(cache_key, code, timeout=300)

        response = self.client.post(self.verify_url, {"email": email, "code": code})

        if response.status_code != 200:
            print(f"Error Detail: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("비밀번호 찾기", response.data["detail"])

        verified_key = f"email_verified:reset_password:{email}"
        self.assertTrue(cache.get(verified_key))

    def test_verify_email_wrong_code(self) -> None:
        cache.set(f"email:reset_password:{self.email}", "asA456", timeout=300)

        response = self.client.post(self.verify_url, {"email": self.email, "code": "000000"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_verify_email_expired(self) -> None:
        response = self.client.post(self.verify_url, {"email": self.email, "code": "asA456"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_verify_email_invalid_email_format(self) -> None:
        response = self.client.post(self.verify_url, {"email": "not-an-email", "code": "asA456"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_verify_email_required_email(self) -> None:
        response = self.client.post(self.verify_url, {"code": "123456"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("email", response.data["error_detail"])
