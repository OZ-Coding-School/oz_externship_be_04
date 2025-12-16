from typing import Any
from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class EmailAuthTestCase(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.send_url = reverse("send-email")
        self.verify_url = reverse("verify-email")
        self.email = "testemail@test.com"

    def tearDown(self) -> None:
        cache.clear()

    @patch("apps.users.utils.send_auth.send_mail")
    def test_send_email_success(self, mock_send_mail: Any) -> None:
        response = self.client.post(self.send_url, {"email": self.email})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        redis_key = f"email:signup:{self.email}"
        self.assertIsNotNone(cache.get(redis_key))

    def test_send_email_invalid_format(self) -> None:
        response = self.client.post(self.send_url, {"email": "not-an-email"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_email_duplicate(self) -> None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
        User.objects.create_user(
            email=self.email,
            password="password",
            nickname="test",
            phone_number="01000000000",
            name="test",
            gender="M",
            birthday="2000-01-01",
        )

        response = self.client.post(self.send_url, {"email": self.email})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_success(self) -> None:
        code = "123456"
        cache.set(f"email:signup:{self.email}", code, timeout=300)

        response = self.client.post(self.verify_url, {"email": self.email, "code": code})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(cache.get(f"verified:email:{self.email}"), True)

    def test_verify_email_wrong_code(self) -> None:
        cache.set(f"email:signup:{self.email}", "123456", timeout=300)

        response = self.client.post(self.verify_url, {"email": self.email, "code": "000000"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_expired(self) -> None:
        response = self.client.post(self.verify_url, {"email": self.email, "code": "123456"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
