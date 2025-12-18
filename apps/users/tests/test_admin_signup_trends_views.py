from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AdminSignupTrendAPITests(APITestCase):

    def setUp(self) -> None:
        self.url = "/api/v1/admin/analytics/signup/trends"

        self.admin_user = User.objects.create_superuser(
            "admin@example.com",
            "adminpass123!",
            name="관리자",
            nickname="admin",
            phone_number="01000000000",
            gender="M",
            profile_img_url="https://example.com/admin.png",
        )

        self.normal_user1 = User.objects.create_user(
            "user1@example.com",
            "userpass123!",
            name="유저1",
            nickname="user1",
            phone_number="01000000001",
            gender="F",
            profile_img_url="https://example.com/user1.png",
            is_active=True,
        )
        self.normal_user2 = User.objects.create_user(
            "user2@example.com",
            "userpass123!",
            name="유저2",
            nickname="user2",
            phone_number="01000000002",
            gender="M",
            profile_img_url="https://example.com/user2.png",
            is_active=True,
        )

    def test_signup_trend_unauthorized(self) -> None:
        response = self.client.get(self.url, {"interval": "monthly"})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_signup_trend_forbidden_for_normal_user(self) -> None:
        self.client.force_authenticate(user=self.normal_user1)

        response = self.client.get(self.url, {"interval": "monthly"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error_detail", response.data)

    def test_signup_trend_monthly_success_for_admin(self) -> None:
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

        expected_total = User.objects.filter(
            created_at__date__gte=from_date,
            created_at__date__lte=to_date,
        ).count()

        self.assertEqual(data["total"], expected_total)

    def test_signup_trend_yearly_success_for_admin(self) -> None:
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

        expected_total = User.objects.filter(
            created_at__date__gte=from_date,
            created_at__date__lte=to_date,
        ).count()

        self.assertEqual(data["total"], expected_total)
