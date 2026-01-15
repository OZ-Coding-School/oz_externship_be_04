from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.users.models.withdrawal import Withdrawal
from apps.users.utils.consts import WithdrawalReason


class AdminWithdrawalTrendAPITests(APITestCase):

    def setUp(self) -> None:
        self.url = "/api/v1/admin/analytics/withdrawals/trends"

        self.normal_user = User.objects.create(
            email="user@example.com",
            password="password123",
            name="일반유저",
            nickname="normal",
            phone_number="01000000001",
            gender="F",
            birthday=date(2000, 1, 1),
            profile_img_url="https://example.com/1.png",
            is_active=False,
        )

        self.staff_user = User.objects.create(
            email="staff@example.com",
            password="password123",
            name="스태프",
            nickname="staff",
            phone_number="01000000002",
            gender="M",
            birthday=date(1995, 1, 1),
            profile_img_url="https://example.com/2.png",
            is_active=True,
            is_staff=True,
        )

        self.super_user = User.objects.create(
            email="admin@example.com",
            password="password123",
            name="관리자",
            nickname="admin",
            phone_number="01000000003",
            gender="M",
            birthday=date(1990, 1, 1),
            profile_img_url="https://example.com/3.png",
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )

        self.withdrawal_1 = Withdrawal.objects.create(
            user=self.normal_user,
            reason=WithdrawalReason.NO_LONGER_NEEDED,
            reason_detail="더 이상 서비스가 필요 없음",
        )
        self.withdrawal_2 = Withdrawal.objects.create(
            user=self.staff_user,
            reason=WithdrawalReason.LACK_OF_INTEREST,
            reason_detail="관심 감소",
        )

    def test_withdrawal_trend_unauthorized_returns_401(self) -> None:
        response = self.client.get(self.url, {"interval": "monthly"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_withdrawal_trend_forbidden_for_normal_user(self) -> None:
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.get(self.url, {"interval": "monthly"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_withdrawal_trend_monthly_success_for_staff(self) -> None:
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(self.url, {"interval": "monthly"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data

        self.assertEqual(data["interval"], "monthly")
        self.assertIn("from_date", data)
        self.assertIn("to_date", data)
        self.assertIn("total", data)
        self.assertIn("items", data)
        self.assertIsInstance(data["items"], list)

        for item in data["items"]:
            self.assertIn("period", item)
            self.assertIn("count", item)

        summed = sum(item["count"] for item in data["items"])
        self.assertEqual(data["total"], summed)

        from_date = date.fromisoformat(data["from_date"])
        to_date = date.fromisoformat(data["to_date"])

        expected_total = Withdrawal.objects.filter(
            withdrawn_at__date__gte=from_date,
            withdrawn_at__date__lte=to_date,
        ).count()

        self.assertEqual(data["total"], expected_total)

    def test_withdrawal_trend_yearly_success_for_staff(self) -> None:
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(self.url, {"interval": "yearly"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data

        self.assertEqual(data["interval"], "yearly")
        self.assertIn("from_date", data)
        self.assertIn("to_date", data)
        self.assertIn("total", data)
        self.assertIn("items", data)
        self.assertIsInstance(data["items"], list)

        for item in data["items"]:
            self.assertIn("period", item)
            self.assertIn("count", item)

        summed = sum(item["count"] for item in data["items"])
        self.assertEqual(data["total"], summed)

        from_date = date.fromisoformat(data["from_date"])
        to_date = date.fromisoformat(data["to_date"])

        expected_total = Withdrawal.objects.filter(
            withdrawn_at__date__gte=from_date,
            withdrawn_at__date__lte=to_date,
        ).count()

        self.assertEqual(data["total"], expected_total)
