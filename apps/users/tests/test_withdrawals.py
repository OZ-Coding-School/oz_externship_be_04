import random
from datetime import date, timedelta
from unittest import TestCase

from django.core.exceptions import ValidationError as DjangoErrorValid
from django.utils import timezone
from rest_framework.exceptions import ValidationError as APIErrorValid

from apps.users.models import User, Withdrawal
from apps.users.services.withdrawal_services import withdraw_service


class WithdrawalCheckModel(TestCase):
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

    def test_withdrawal(self) -> None:
        expected_date = timezone.now().date() + timedelta(days=14)
        withdrawal = Withdrawal.objects.create(
            user=self.user,
            reason="TOO_DIFFICULT",
            reason_detail="탈퇴 사유 상세 작성 (500자 까지 허용)",
        )
        self.assertEqual(withdrawal.due_date, expected_date)

    def test_withdrawal_reason_blank(self) -> None:
        withdrawal = Withdrawal(
            user=self.user,
            reason="LACK_OF_INTEREST",
            reason_detail="",
        )

        with self.assertRaises(DjangoErrorValid):
            withdrawal.full_clean()

    def test_withdrawal_reason_invalid_choice(self) -> None:
        withdrawal = Withdrawal(
            user=self.user,
            reason="I_DONT_WANT_TO_STUDY_ANYMORE",
            reason_detail="test detail",
        )

        with self.assertRaises(DjangoErrorValid):
            withdrawal.full_clean()

    def test_withdrawal_max_length_check(self) -> None:
        withdrawal = Withdrawal(
            user=self.user,
            reason="NO_LONGER_NEEDED",
            reason_detail="a" * 501,
        )

        with self.assertRaises(DjangoErrorValid):
            withdrawal.full_clean()


class WithdrawalCheckService(TestCase):
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

    def test_withdrawal_is_active_false(self) -> None:
        self.user.is_active = False
        self.user.save()
        data = {
            "reason": "TOO_DIFFICULT",
            "reason_detail": "이미 탈퇴한 유저 테스트 입니다.",
        }
        with self.assertRaises(APIErrorValid):
            withdraw_service(self.user, data)

        self.assertEqual(Withdrawal.objects.count(), 0)
