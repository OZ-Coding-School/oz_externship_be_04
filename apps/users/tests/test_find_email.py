from unittest.mock import MagicMock, patch

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models.users import User
from apps.users.views.find_email_view import FindEmailView


class FindEmailTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()

        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="test1234",
            name="홍길동",
            nickname="테스터",
            phone_number="01012345678",
            gender="M",
        )

    def tearDown(self) -> None:
        cache.clear()
        User.objects.all().delete()

    @patch("apps.users.utils.send_sms.Client")
    def test_find_email_success(self, mock_client: MagicMock) -> None:
        mock_verification_check = MagicMock()
        mock_verification_check.status = "approved"
        mock_client.return_value.verify.v2.services.return_value.verification_checks.create.return_value = (
            mock_verification_check
        )

        url = "/api/v1/accounts/find-email"
        data = {"phone_number": "01012345678", "code": "123456"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["detail"], "계정찾기 성공.")
        self.assertTrue("***" in response.data["email"])

    @patch("apps.users.utils.send_sms.Client")
    def test_find_email_invalid_code(self, mock_client: MagicMock) -> None:
        mock_verification_check = MagicMock()
        mock_verification_check.status = "pending"
        mock_client.return_value.verify.v2.services.return_value.verification_checks.create.return_value = (
            mock_verification_check
        )

        url = "/api/v1/accounts/find-email"
        data = {"phone_number": "01012345678", "code": "000000"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("code", response.data["error_detail"])

    @patch("apps.users.utils.send_sms.Client")
    def test_find_email_phone_not_found(self, mock_client: MagicMock) -> None:
        mock_verification_check = MagicMock()
        mock_verification_check.status = "approved"
        mock_client.return_value.verify.v2.services.return_value.verification_checks.create.return_value = (
            mock_verification_check
        )

        url = "/api/v1/accounts/find-email"
        data = {"phone_number": "01099999999", "code": "123456"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertEqual(response.data["error_detail"], "등록된 전화번호가 없습니다.")

    def test_find_email_required_phone(self) -> None:
        url = "/api/v1/accounts/find-email"
        data = {"code": "123456"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("phone_number", response.data["error_detail"])

    def test_find_email_required_code(self) -> None:
        url = "/api/v1/accounts/find-email"
        data = {"phone_number": "01012345678"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("code", response.data["error_detail"])

    def test_find_email_invalid_phone_format(self) -> None:
        url = "/api/v1/accounts/find-email"
        data = {"phone_number": "123456", "code": "123456"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("phone_number", response.data["error_detail"])

    def test_email_masking(self) -> None:

        masked = FindEmailView._mask_email("asd@example.com")
        self.assertEqual(masked, "a***@example.com")

        masked = FindEmailView._mask_email("asdasdasd@example.com")
        self.assertEqual(masked, "asd***@example.com")

        masked = FindEmailView._mask_email("asd@example.com")
        self.assertEqual(masked, "a***@example.com")
