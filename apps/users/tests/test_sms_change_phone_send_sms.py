from typing import Any
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models.users import User
from apps.users.utils.send_sms import TwilioSendSms


class SMSAuthTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()

        self.user = User.objects.create_user(
            email="test@example.com",
            password="test1234",
            name="홍길동",
            nickname="테스터",
            phone_number="01012345678",
            gender="M",
        )
        self.phone_number = "01012345678"

    def tearDown(self) -> None:
        cache.clear()
        User.objects.all().delete()


@patch("apps.users.utils.send_sms.Client")
def test_change_phone_send_sms_success(self: Any, mock_client: MagicMock) -> None:
    mock_verification = MagicMock()
    mock_verification.status = "pending"
    mock_client.return_value.verify.v2.services.return_value.verifications.create.return_value = mock_verification

    self.client.force_authenticate(user=self.user)

    url = "/api/v1/accounts/change-phone/send-sms"
    data = {"phone_number": "01011112222"}

    response = self.client.post(url, data, format="json")

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertIn("detail", response.data)
    self.assertIn("휴대폰 번호 변경", response.data["detail"])


def test_change_phone_send_sms_fail_unauthorized(self: Any) -> None:
    url = "/api/v1/accounts/change-phone/send-sms"
    data = {"phone_number": "01011112222"}

    response = self.client.post(url, data, format="json")

    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


def test_change_phone_send_sms_fail_duplicate(self: Any) -> None:
    self.client.force_authenticate(user=self.user)

    url = "/api/v1/accounts/change-phone/send-sms"
    data = {"phone_number": "01099999999"}

    response = self.client.post(url, data, format="json")

    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertIn("error_detail", response.data)


@patch("apps.users.utils.send_sms.Client")
def test_change_phone_send_sms_success_own_number(self: Any, mock_client: MagicMock) -> None:
    mock_verification = MagicMock()
    mock_verification.status = "pending"
    mock_client.return_value.verify.v2.services.return_value.verifications.create.return_value = mock_verification

    self.client.force_authenticate(user=self.user)

    url = "/api/v1/accounts/change-phone/send-sms"
    data = {"phone_number": "01012345678"}

    response = self.client.post(url, data, format="json")

    self.assertEqual(response.status_code, status.HTTP_200_OK)


def test_change_phone_send_sms_fail_invalid_format(self: Any) -> None:
    self.client.force_authenticate(user=self.user)

    url = "/api/v1/accounts/change-phone/send-sms"
    data = {"phone_number": "123456"}

    response = self.client.post(url, data, format="json")

    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertIn("error_detail", response.data)


def test_change_phone_send_sms_fail_required(self: Any) -> None:
    self.client.force_authenticate(user=self.user)

    url = "/api/v1/accounts/change-phone/send-sms"
    data: dict[str, Any] = {}

    response = self.client.post(url, data, format="json")

    self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    self.assertIn("error_detail", response.data)
