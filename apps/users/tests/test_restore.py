import random
from typing import Any
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import Withdrawal
from apps.users.serializers.restore_serializers import (
    RestoreEmailCodeSerializer,
    RestoreWithdrawalSerializer,
)

User = get_user_model()


class RestoreSerializerCheck(TransactionTestCase):
    def setUp(self) -> None:
        uid = random.randint(1000, 9999)

        self.inactive_user = User.objects.create(
            email=f"testet{uid}@test01.com",
            nickname=f"testet{uid}",
            phone_number=f"0101234{uid}",
            password="password",
            is_active=False,
        )

        Withdrawal.objects.create(
            user=self.inactive_user,
            reason="TOO_DIFFICULT",
            reason_detail="serializer test withdrawal",
            due_date=timezone.now().date(),
            withdrawn_at=timezone.now(),
        )

        self.active_user = User.objects.create(
            email=f"tested{uid}@test02.com",
            nickname=f"tested{uid}",
            phone_number=f"0104321{uid}",
            password="password",
            is_active=True,
        )

    def test_restore_serializer_email_valid(self) -> None:
        data = {"email": self.inactive_user.email}
        serializer = RestoreWithdrawalSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_restore_serializer_email_not_found(self) -> None:
        data = {"email": "unknown@test.com"}
        serializer = RestoreWithdrawalSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertIn("error_detail", serializer.errors["email"])
        self.assertEqual(serializer.errors["email"]["error_detail"][0], "가입된 이메일이 아닙니다.")

    def test_restore_serializer_already_active(self) -> None:
        data = {"email": self.active_user.email}
        serializer = RestoreWithdrawalSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertIn("error_detail", serializer.errors["email"])
        self.assertEqual(serializer.errors["email"]["error_detail"][0], "이미 활성화된 유저입니다.")

    @patch("apps.users.utils.auth_code.AuthCodeCache.verify")
    def test_restore_code_serializer_save(self, mock_verify: Any) -> None:
        mock_verify.return_value = True

        data = {"email": self.inactive_user.email, "code": "123456"}
        serializer = RestoreEmailCodeSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.inactive_user.refresh_from_db()

        self.assertTrue(user.is_active)
        self.assertTrue(self.inactive_user.is_active)
        self.assertEqual(Withdrawal.objects.filter(user=self.inactive_user).count(), 0)

    @patch("apps.users.utils.auth_code.AuthCodeCache.verify")
    def test_restore_code_serializer_invalid_code(self, mock_verify: Any) -> None:
        mock_verify.return_value = False

        data = {"email": self.inactive_user.email, "code": "000000"}
        serializer = RestoreEmailCodeSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("error_detail", serializer.errors)


class RestoreViewCheck(APITestCase):
    def setUp(self) -> None:
        uid = random.randint(1000, 9999)

        self.user = User.objects.create(
            email=f"testts{uid}@test03.com",
            nickname=f"testts{uid}",
            phone_number=f"0100987{uid}",
            password="password",
            is_active=False,
        )

        Withdrawal.objects.create(
            user=self.user,
            reason="ETC",
            reason_detail="view test withdrawal",
            due_date=timezone.now().date(),
            withdrawn_at=timezone.now(),
        )

    @patch("apps.users.utils.send_auth.SendAuth.send_restore_email")
    def test_restore_send_email_view_success(self, mock_send_email: Any) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_send_email.return_value = mock_response

        try:
            url = reverse("restore-send-email")
        except:
            url = "/api/v1/accounts/restore/send-email"

        data = {"email": self.user.email}
        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "계정복구를 위한 이메일 인증 코드가 전송되었습니다.")

    @patch("apps.users.utils.auth_code.AuthCodeCache.verify")
    def test_restore_account_view_success(self, mock_verify: Any) -> None:
        mock_verify.return_value = True

        try:
            url = reverse("restore-account")
        except:
            url = "/api/v1/accounts/restore"

        data = {"email": self.user.email, "code": "123456"}
        response = self.client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "계정복구가 완료되었습니다.")

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
