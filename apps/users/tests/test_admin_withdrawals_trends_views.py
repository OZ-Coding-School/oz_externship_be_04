from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models.withdrawal import Withdrawal
from apps.users.utils.reason_choices import WithdrawalReason

User = get_user_model()


class AdminWithdrawalTrendAPITests(APITestCase):

    def setUp(self) -> None:
        self.url = "/api/v1/admin/analytics/withdrawals/trends"

        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123!",
            name="관리자",
            nickname="admin",
            phone_number="01000000000",
            gender="M",
            profile_img_url="https://example.com/admin.png",
        )

        self.normal_user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="userpass123!",
            name="유저1",
            nickname="user1",
            phone_number="01000000001",
            gender="F",
            profile_img_url="https://example.com/user1.png",
            is_active=False,
        )
        self.normal_user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="userpass123!",
            name="유저2",
            nickname="user2",
            phone_number="01000000002",
            gender="M",
            profile_img_url="https://example.com/user2.png",
            is_active=False,
        )

        Withdrawal.objects.create(
            user=self.normal_user1,
            reason=WithdrawalReason.OTHER,
            reason_detail="기타 사유 1",
        )
        Withdrawal.objects.create(
            user=self.normal_user2,
            reason=WithdrawalReason.NO_LONGER_NEEDED,
            reason_detail="더 이상 서비스가 필요 없음",
        )

        self.active_normal_user = User.objects.create_user(
            username="active_user",
            email="active_user@example.com",
            password="userpass123!",
            name="일반유저",
            nickname="active_user",
            phone_number="01000000003",
            gender="F",
            profile_img_url="https://example.com/active_user.png",
            is_active=True,
        )

    def test_withdrawal_trend_unauthorized(self) -> None:
        response = self.client.get(self.url, {"interval": "monthly"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_withdrawal_trend_forbidden_for_normal_user(self) -> None:
        self.client.force_authenticate(user=self.active_normal_user)

        response = self.client.get(self.url, {"interval": "monthly"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_withdrawal_trend_monthly_success_for_admin(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

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

    def test_withdrawal_trend_yearly_success_for_admin(self) -> None:
        self.client.force_authenticate(user=self.admin_user)

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
