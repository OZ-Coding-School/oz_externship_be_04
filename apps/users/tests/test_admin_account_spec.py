from datetime import date

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AdminAccountBaseTestCase(APITestCase):
    def setUp(self) -> None:
        self.normal_user = User.objects.create(
            email="user@example.com",
            password="password123",
            name="일반유저",
            nickname="normal",
            phone_number="01000000001",
            gender="F",
            birthday=date(2000, 1, 1),
            profile_img_url="https://example.com/1.png",
            is_active=True,
        )

        self.admin_user = User.objects.create(
            email="admin@example.com",
            password="password123",
            name="관리자",
            nickname="admin",
            phone_number="01000000002",
            gender="M",
            birthday=date(1990, 1, 1),
            profile_img_url="https://example.com/2.png",
            is_active=True,
            is_staff=True,
        )


class AdminAccountListSpecTests(AdminAccountBaseTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("admin_account_list")

    def test_admin_account_list_forbidden_for_normal_user(self) -> None:

        self.client.force_authenticate(user=self.normal_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_account_list_success_for_admin(self) -> None:

        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data

        for key in ["count", "next", "previous", "results"]:
            self.assertIn(key, data)

        results = data["results"]
        self.assertIsInstance(results, list)

        if results:
            first = results[0]
            for field in [
                "id",
                "email",
                "nickname",
                "name",
                "birthday",
                "status",
                "role",
                "withdraw_at",
                "created_at",
            ]:
                self.assertIn(field, first)


class AdminAccountDetailSpecTests(AdminAccountBaseTestCase):

    def test_detail_forbidden_for_normal_user(self) -> None:

        self.client.force_authenticate(user=self.normal_user)

        url = reverse("admin_account_detail", kwargs={"account_id": self.normal_user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_success_for_admin(self) -> None:

        self.client.force_authenticate(user=self.admin_user)

        url = reverse("admin_account_detail", kwargs={"account_id": self.normal_user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data

        for field in [
            "id",
            "name",
            "gender",
            "nickname",
            "birthday",
            "phone_number",
            "email",
            "role",
            "status",
            "created_at",
            "profile_img_url",
        ]:
            self.assertIn(field, data)

    def test_detail_not_found_for_admin(self) -> None:

        self.client.force_authenticate(user=self.admin_user)

        url = reverse("admin_account_detail", kwargs={"account_id": 999999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
