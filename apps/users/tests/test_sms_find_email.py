from unittest.mock import MagicMock, patch

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models.users import User


class SMSViewTestCase(APITestCase):
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

        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="test1234",
            name="김철수",
            nickname="다른테스터",
            phone_number="01099999999",
            gender="M",
        )

    def tearDown(self) -> None:
        cache.clear()
        User.objects.all().delete()

    @patch("apps.users.utils.send_sms.Client")
    def test_find_email_send_sms_success(self, mock_client: MagicMock) -> None:
        mock_verification = MagicMock()
        mock_verification.status = "pending"
        mock_client.return_value.verify.v2.services.return_value.verifications.create.return_value = mock_verification

        url = "/api/v1/accounts/find-email/send-sms"
        data = {"name": "홍길동", "phone_number": "01012345678"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertIn("계정찾기", response.data["detail"])

    def test_find_email_send_sms_fail_user_not_found(self) -> None:
        url = "/api/v1/accounts/find-email/send-sms"
        data = {"name": "없는사람", "phone_number": "01011112222"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_find_email_send_sms_fail_invalid_phone(self) -> None:
        url = "/api/v1/accounts/find-email/send-sms"
        data = {"name": "홍길동", "phone_number": "123456"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_find_email_send_sms_fail_required_name(self) -> None:
        url = "/api/v1/accounts/find-email/send-sms"
        data = {"phone_number": "01012345678"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("name", response.data["error_detail"])

    def test_find_email_send_sms_fail_required_phone(self) -> None:
        url = "/api/v1/accounts/find-email/send-sms"
        data = {"name": "홍길동"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("phone_number", response.data["error_detail"])

    @patch("apps.users.utils.send_sms.Client")
    def test_find_email_send_sms_with_hyphen(self, mock_client: MagicMock) -> None:
        mock_verification = MagicMock()
        mock_verification.status = "pending"
        mock_client.return_value.verify.v2.services.return_value.verifications.create.return_value = mock_verification

        url = "/api/v1/accounts/find-email/send-sms"
        data = {"name": "홍길동", "phone_number": "010-1234-5678"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
