from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.users.models.withdrawal import Withdrawal
from apps.users.utils.reason_choices import WithdrawalReason


class AdminWithdrawalBaseTestCase(APITestCase):
    def setUp(self) -> None:
        self.normal_user = User.objects.create_user(
            email="normal@test.com",
            password="testpass123",
            name="일반유저",
            nickname="normal_user",
            phone_number="01000000001",
            gender="M",
        )

        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            password="testpass123",
            name="스태프유저",
            nickname="staff_user",
            phone_number="01000000002",
            gender="F",
        )
        self.staff_user.is_staff = True
        self.staff_user.save()

        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpass123",
            name="관리자유저",
            nickname="admin_user",
            phone_number="01000000003",
            gender="M",
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()

        self.withdrawal_1 = Withdrawal.objects.create(
            user=self.normal_user,
            reason=WithdrawalReason.NO_LONGER_NEEDED,
        )
        self.withdrawal_2 = Withdrawal.objects.create(
            user=self.staff_user,
            reason=WithdrawalReason.LACK_OF_INTEREST,
        )

        self.withdrawal_without_user = Withdrawal.objects.create(
            user=None,
            reason=WithdrawalReason.OTHER,
        )

        self.list_url = reverse("admin_withdrawal_list")


class AdminWithdrawalListTests(AdminWithdrawalBaseTestCase):
    def test_admin_withdrawal_list_unauthenticated_returns_401(self) -> None:
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_admin_withdrawal_list_forbidden_for_normal_user(self) -> None:
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_admin_withdrawal_list_success_for_staff_user(self) -> None:
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)

        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 3)

        item = response.data["results"][0]
        self.assertIn("id", item)
        self.assertIn("email", item)
        self.assertIn("name", item)
        self.assertIn("role", item)
        self.assertIn("birthday", item)
        self.assertIn("reason", item)
        self.assertIn("withdrawn_at", item)

    def test_admin_withdrawal_list_search_by_email(self) -> None:
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(self.list_url, {"search": "normal@test.com"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["email"],
            "normal@test.com",
        )

    def test_admin_withdrawal_list_filter_by_role_user(self) -> None:
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(self.list_url, {"role": "user"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["email"],
            "normal@test.com",
        )

    def test_admin_withdrawal_list_filter_by_reason(self) -> None:
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(
            self.list_url,
            {"reason": WithdrawalReason.LACK_OF_INTEREST},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["reason"],
            WithdrawalReason.LACK_OF_INTEREST,
        )

    def test_admin_withdrawal_list_sort_latest(self) -> None:
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(self.list_url, {"sort": "latest"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_admin_withdrawal_list_sort_oldest(self) -> None:
        self.client.force_authenticate(user=self.staff_user)

        response = self.client.get(self.list_url, {"sort": "oldest"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)


class AdminWithdrawalDetailTests(AdminWithdrawalBaseTestCase):
    def test_admin_withdrawal_detail_unauthenticated_returns_401(self) -> None:
        url = reverse(
            "admin_withdrawal_detail",
            args=[self.withdrawal_1.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_admin_withdrawal_detail_forbidden_for_normal_user(self) -> None:
        self.client.force_authenticate(user=self.normal_user)
        url = reverse(
            "admin_withdrawal_detail",
            args=[self.withdrawal_1.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_admin_withdrawal_detail_success_for_staff_user(self) -> None:
        self.client.force_authenticate(user=self.staff_user)
        url = reverse(
            "admin_withdrawal_detail",
            args=[self.withdrawal_1.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["id"], self.withdrawal_1.id)
        self.assertEqual(data["reason"], self.withdrawal_1.reason)
        self.assertEqual(data["reason_detail"], self.withdrawal_1.reason_detail)
        self.assertIn("user", data)
        user_data = data["user"]
        self.assertEqual(user_data["id"], self.normal_user.id)
        self.assertEqual(user_data["email"], self.normal_user.email)
        self.assertEqual(user_data["nickname"], self.normal_user.nickname)
        self.assertEqual(user_data["name"], self.normal_user.name)

    def test_admin_withdrawal_detail_not_found_returns_404_when_invalid_id(self) -> None:
        self.client.force_authenticate(user=self.staff_user)
        url = reverse("admin_withdrawal_detail", args=[999999])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", response.data)

    def test_admin_withdrawal_detail_not_found_when_user_is_none(self) -> None:
        self.client.force_authenticate(user=self.staff_user)
        url = reverse(
            "admin_withdrawal_detail",
            args=[self.withdrawal_without_user.id],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", response.data)
