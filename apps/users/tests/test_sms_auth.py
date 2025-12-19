from unittest.mock import MagicMock, patch

from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.utils.send_sms import TwilioSendSms


class SMSAuthTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()
        self.phone_number = "01012345678"

    def tearDown(self) -> None:
        cache.clear()

    @patch("apps.users.utils.send_sms.Client")
    def test_sms_send_success(self, mock_client: MagicMock) -> None:
        mock_verification = MagicMock()
        mock_verification.status = "pending"
        mock_client.return_value.verify.v2.services.return_value.verifications.create.return_value = mock_verification

        response = TwilioSendSms.send_signup_sms(self.phone_number)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("회원가입", response.data["detail"])

    @patch("apps.users.utils.send_sms.Client")
    def test_sms_verify_success(self, mock_client: MagicMock) -> None:
        mock_verification_check = MagicMock()
        mock_verification_check.status = "approved"
        mock_client.return_value.verify.v2.services.return_value.verification_checks.create.return_value = (
            mock_verification_check
        )

        response = TwilioSendSms.verify_code(self.phone_number, "123456", "signup")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(TwilioSendSms.is_verified(self.phone_number, "signup"))

    @patch("apps.users.utils.send_sms.Client")
    def test_sms_verify_fail(self, mock_client: MagicMock) -> None:
        mock_verification_check = MagicMock()
        mock_verification_check.status = "pending"
        mock_client.return_value.verify.v2.services.return_value.verification_checks.create.return_value = (
            mock_verification_check
        )

        response = TwilioSendSms.verify_code(self.phone_number, "000000", "signup")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(TwilioSendSms.is_verified(self.phone_number, "signup"))

    def test_verify_check(self) -> None:
        self.assertFalse(TwilioSendSms.is_verified(self.phone_number, "signup"))

        cache_key = f"sms_verified:signup:{self.phone_number}"
        cache.set(cache_key, True, timeout=300)

        self.assertTrue(TwilioSendSms.is_verified(self.phone_number, "signup"))

    def test_verify_cache_delete(self) -> None:
        cache_key = f"sms_verified:signup:{self.phone_number}"
        cache.set(cache_key, True, timeout=300)

        self.assertTrue(TwilioSendSms.is_verified(self.phone_number, "signup"))

        TwilioSendSms.clear_verification(self.phone_number, "signup")

        self.assertFalse(TwilioSendSms.is_verified(self.phone_number, "signup"))
