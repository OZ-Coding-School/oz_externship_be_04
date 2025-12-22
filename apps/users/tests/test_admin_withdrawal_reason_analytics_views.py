from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.users.models.withdrawal import Withdrawal
from apps.users.utils.reason_choices import WithdrawalReason


class AdminWithdrawalReasonAnalyticsBaseTestCase(APITestCase):

    def setUp(self) -> None:
        self.percentage_url = reverse("admin_withdrawal_reason_percentage")
        self.monthly_stats_url = reverse("admin_withdrawal_reasons_stats_monthly")

        self.normal_user = User.objects.create_user(
            email="normal@test.com",
            password="testpass123!",
            name="일반유저",
            nickname="normal",
            phone_number="01000000001",
            gender="M",
        )

        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="testpass123!",
            name="스태프유저",
            nickname="staff",
            phone_number="01000000002",
            gender="F",
        )
        self.staff_user.is_staff = True
        self.staff_user.is_active = True
        self.staff_user.save()

        self.withdraw_user1 = User.objects.create_user(
            email="withdraw1@test.com",
            password="testpass123!",
            name="탈퇴유저1",
            nickname="withdraw1",
            phone_number="01000000003",
            gender="M",
        )
        self.withdraw_user2 = User.objects.create_user(
            email="withdraw2@test.com",
            password="testpass123!",
            name="탈퇴유저2",
            nickname="withdraw2",
            phone_number="01000000004",
            gender="F",
        )

        Withdrawal.objects.create(
            user=self.withdraw_user1,
            reason=WithdrawalReason.OTHER,
            reason_detail="기타 사유 1",
        )
        Withdrawal.objects.create(
            user=self.withdraw_user2,
            reason=WithdrawalReason.OTHER,
            reason_detail="기타 사유 2",
        )

        Withdrawal.objects.create(
            user=self.withdraw_user1,
            reason=WithdrawalReason.LACK_OF_CONTENT,
            reason_detail="콘텐츠 부족으로 인한 탈퇴",
        )

    def authenticate_as_staff(self) -> None:
        self.client.force_authenticate(user=self.staff_user)

    def authenticate_as_normal(self) -> None:
        self.client.force_authenticate(user=self.normal_user)


class AdminWithdrawalReasonPercentageAPITests(AdminWithdrawalReasonAnalyticsBaseTestCase):
    """
    전체 기간 회원 탈퇴 사유 Percentage 분석 API 테스트
    """

    def test_withdrawal_reason_percentage_unauthorized_returns_401(self) -> None:

        response = self.client.get(self.percentage_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_withdrawal_reason_percentage_forbidden_for_normal_user(self) -> None:
        self.authenticate_as_normal()

        response = self.client.get(self.percentage_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_withdrawal_reason_percentage_success_for_staff(self) -> None:

        self.authenticate_as_staff()

        response = self.client.get(self.percentage_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data

        for key in ["from_date", "to_date", "total", "items"]:
            self.assertIn(key, data)

        self.assertIsInstance(data["items"], list)

        summed = sum(item["count"] for item in data["items"])
        self.assertEqual(data["total"], summed)

        from_date = date.fromisoformat(data["from_date"])
        to_date = date.fromisoformat(data["to_date"])
        self.assertLessEqual(from_date, to_date)

        items_by_reason = {item["reason"]: item for item in data["items"]}

        self.assertIn(WithdrawalReason.OTHER, items_by_reason)
        self.assertIn(WithdrawalReason.LACK_OF_CONTENT, items_by_reason)

        self.assertEqual(items_by_reason[WithdrawalReason.OTHER]["count"], 2)
        self.assertEqual(items_by_reason[WithdrawalReason.LACK_OF_CONTENT]["count"], 1)

        total_percentage = sum(item["percentage"] for item in data["items"])
        self.assertTrue(90.0 <= total_percentage <= 110.0)


class AdminWithdrawalReasonMonthlyStatsAPITests(AdminWithdrawalReasonAnalyticsBaseTestCase):

    def test_withdrawal_reason_monthly_stats_unauthorized_returns_401(self) -> None:
        response = self.client.get(
            self.monthly_stats_url,
            {"reason": WithdrawalReason.OTHER},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_withdrawal_reason_monthly_stats_forbidden_for_normal_user(self) -> None:
        self.authenticate_as_normal()

        response = self.client.get(
            self.monthly_stats_url,
            {"reason": WithdrawalReason.OTHER},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_withdrawal_reason_monthly_stats_missing_reason_returns_400(self) -> None:
        self.authenticate_as_staff()

        response = self.client.get(self.monthly_stats_url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_withdrawal_reason_monthly_stats_success_for_staff(self) -> None:
        self.authenticate_as_staff()

        reason = WithdrawalReason.OTHER

        response = self.client.get(
            self.monthly_stats_url,
            {"reason": reason},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data

        for key in ["reason", "reason_label", "from_date", "to_date", "total", "items"]:
            self.assertIn(key, data)

        self.assertEqual(data["reason"], reason)
        self.assertIsInstance(data["items"], list)

        summed = sum(item["count"] for item in data["items"])
        self.assertEqual(data["total"], summed)

        from_date = date.fromisoformat(data["from_date"])
        to_date = date.fromisoformat(data["to_date"])
        self.assertLessEqual(from_date, to_date)

        expected_total = Withdrawal.objects.filter(
            reason=reason,
            withdrawn_at__date__gte=from_date,
            withdrawn_at__date__lte=to_date,
        ).count()

        self.assertEqual(data["total"], expected_total)

        if data["items"]:
            sample_period = data["items"][0]["period"]
            self.assertEqual(len(sample_period), 7)
            self.assertEqual(sample_period[4], "-")
