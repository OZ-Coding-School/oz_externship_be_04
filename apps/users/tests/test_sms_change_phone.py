from unittest.mock import MagicMock, patch

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.utils.send_sms import TwilioSendSms
from apps.users.models.users import User


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
    def test_change_phone_success(self, mock_client: MagicMock) -> None:
        mock_verification_check = MagicMock()
        mock_verification_check.status = "approved"
        mock_client.return_value.verify.v2.services.return_value.verification_checks.create.return_value = (
            mock_verification_check
        )

        self.client.force_authenticate(user=self.user)

        url = "/api/v1/accounts/change-phone"
        data = {"phone_number": "01011112222", "code": "123456"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, "01011112222")

    @patch("apps.users.utils.send_sms.Client")
    def test_change_phone_fail_invalid_code(self, mock_client: MagicMock) -> None:
        mock_verification_check = MagicMock()
        mock_verification_check.status = "pending"
        mock_client.return_value.verify.v2.services.return_value.verification_checks.create.return_value = (
            mock_verification_check
        )

        self.client.force_authenticate(user=self.user)

        url = "/api/v1/accounts/change-phone"
        data = {"phone_number": "01011112222", "code": "000000"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, "01012345678")

    def test_change_phone_fail_unauthorized(self) -> None:
        url = "/api/v1/accounts/change-phone"
        data = {"phone_number": "01011112222", "code": "123456"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_phone_fail_duplicate(self) -> None:
        self.client.force_authenticate(user=self.user)

        url = "/api/v1/accounts/change-phone"
        data = {"phone_number": "01099999999", "code": "123456"}  # other_user의 번호

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_change_phone_fail_required_code(self) -> None:
        self.client.force_authenticate(user=self.user)

        url = "/api/v1/accounts/change-phone"
        data = {"phone_number": "01011112222"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)