import random
from datetime import date, timedelta
from unittest import TestCase

from django.core.exceptions import ValidationError as DjangoErrorValid
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError as APIErrorValid
from rest_framework.test import APITestCase

from apps.users.models import User, Withdrawal
from apps.users.services.withdrawal_services import (
    AlreadyLockedAccount,
    withdraw_service,
)


# model 테스트
class WithdrawalCheckModel(TestCase):
    # 기본 user 셋팅
    def setUp(self) -> None:
        uid = random.randint(1000, 9999)

        self.user = User.objects.create(
            email=f"mail{uid}@test.com",
            password="1q2w3e4r!",
            nickname=f"nick{uid}",
            name=f"testname",
            phone_number=f"0108765{uid}",
            birthday=date(2020, 1, 1),
            gender="M",
        )

    # 탈퇴 성공 case + 날짜 계산
    def test_withdrawal(self) -> None:
        expected_date = timezone.now().date() + timedelta(days=14)
        withdrawal = Withdrawal.objects.create(
            user=self.user,
            reason="TOO_DIFFICULT",
            reason_detail="탈퇴 사유 상세 작성 (500자 까지 허용)",
        )
        self.assertEqual(withdrawal.due_date, expected_date)

    # 탈퇴 상세 사유 공백 (실패 case)
    def test_withdrawal_reason_blank(self) -> None:
        withdrawal = Withdrawal(
            user=self.user,
            reason="LACK_OF_INTEREST",
            reason_detail="",
        )

        with self.assertRaises(DjangoErrorValid):
            withdrawal.full_clean()

    # 목록에 없는 일반 탈퇴 사유 선택 ( 실패 case )
    def test_withdrawal_reason_invalid_choice(self) -> None:
        withdrawal = Withdrawal(
            user=self.user,
            reason="I_DONT_WANT_TO_STUDY_ANYMORE",
            reason_detail="test detail",
        )

        with self.assertRaises(DjangoErrorValid):
            withdrawal.full_clean()

    # 탈퇴 상세 사유 500자 초과 시키기 ( 실패 case )
    def test_withdrawal_max_length_check(self) -> None:
        withdrawal = Withdrawal(
            user=self.user,
            reason="NO_LONGER_NEEDED",
            reason_detail="a" * 501,
        )

        with self.assertRaises(DjangoErrorValid):
            withdrawal.full_clean()


# service 테스트
class WithdrawalCheckService(TransactionTestCase):
    def setUp(self) -> None:
        uid = random.randint(1000, 9999)

        self.user = User.objects.create(
            email=f"mail{uid}@test.com",
            password="1q2w3e4r!",
            nickname=f"nick{uid}",
            name=f"testname",
            phone_number=f"0108765{uid}",
            birthday=date(2020, 1, 1),
            gender="M",
            is_active=True,
        )

    # 탈퇴 처리 후 is_active 처리 테스트 ( 초기화 후 데이터 반영 확인 )
    def test_withdrawal_is_active_true(self) -> None:
        data = {
            "reason": "TOO_DIFFICULT",
            "reason_detail": "탈퇴 active test 입니다.",
        }
        result = withdraw_service(self.user, data)

        self.assertIsNotNone(result.id)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(Withdrawal.objects.count(), 1)

    # 이미 탈퇴 처리된 유저가 다시 탈퇴 신청 할때 ( 실패 case )
    def test_withdrawal_is_active_false(self) -> None:
        self.user.is_active = False
        self.user.save()
        data = {
            "reason": "TOO_DIFFICULT",
            "reason_detail": "이미 탈퇴한 유저 테스트 입니다.",
        }
        with self.assertRaises(AlreadyLockedAccount):
            withdraw_service(self.user, data)

        self.assertEqual(Withdrawal.objects.count(), 0)


# view 테스트
class WithdrawalCheckView(APITestCase):
    def setUp(self) -> None:
        uid = random.randint(1000, 9999)

        self.user = User.objects.create(
            email=f"mail{uid}@test.com",
            password="1q2w3e4r!",
            nickname=f"nick{uid}",
            name=f"testname",
            phone_number=f"0108765{uid}",
            birthday=date(2020, 1, 1),
            gender="M",
            is_active=True,
        )

    # 탈퇴 성공 case
    def test_withdrawal_view_success(self) -> None:
        url = "/api/v1/accounts/me"
        self.client.force_authenticate(user=self.user)
        data = {
            "reason": "TOO_DIFFICULT",
            "reason_detail": "view 탈퇴 성공 테스트 입니다.",
            "agree_check": True,
        }
        response = self.client.delete(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(Withdrawal.objects.count(), 1)

    # 회원 탈퇴 동의 안했을 경우 ( 실패 case )
    def test_withdrawal_view_without_agree_check(self) -> None:
        url = "/api/v1/accounts/me"
        self.client.force_authenticate(user=self.user)
        data = {
            "reason": "TOO_DIFFICULT",
            "reason_detail": "동의 하지 않을 경우 탈퇴 실패 테스트 입니다.",
            "agree_check": False,
        }
        response = self.client.delete(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(Withdrawal.objects.count(), 0)
        self.assertIn("error_detail", response.data)
        self.assertEqual(response.data["error_detail"]["agree_check"][0], "회원 탈퇴에 동의해야 탈퇴 가능합니다.")

    # 이미 탈퇴한 회원이 다시 탈퇴 신청을 할 경우 ( 실패 case )
    def test_withdrawal_view_already_active(self) -> None:
        url = "/api/v1/accounts/me"
        self.client.force_authenticate(user=self.user)
        self.user.is_active = False
        self.user.save()

        data = {
            "reason": "TOO_DIFFICULT",
            "reason_detail": "이미 탈퇴 처리된 유저 실패 테스트 입니다.",
            "agree_check": True,
        }
        response = self.client.delete(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertEqual(Withdrawal.objects.count(), 0)
        self.assertIn("error_detail", response.data)
        self.assertEqual(
            response.data["error_detail"],
            (
                {
                    "non_field_errors": [
                        "이미 탈퇴 처리된 유저 입니다. 다시 로그인 하시면 계정 복구를 진행하실 수 있습니다."
                    ]
                }
            ),
        )
