from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User


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

    def authenticate_as_normal_user(self) -> None:
        """일반 유저로 인증"""
        self.client.force_authenticate(user=self.normal_user)

    def authenticate_as_staff_user(self) -> None:
        """스태프 유저로 인증"""
        self.client.force_authenticate(user=self.staff_user)

    def authenticate_as_super_user(self) -> None:
        """슈퍼유저로 인증"""
        self.client.force_authenticate(user=self.super_user)


class AdminAccountListTests(AdminAccountBaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url = reverse("admin_account_list")

    def test_list_unauthenticated_returns_401(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_list_forbidden_for_normal_user(self) -> None:
        self.authenticate_as_normal_user()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_success_for_staff(self) -> None:
        self.authenticate_as_staff_user()

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

    def test_list_filter_by_status_active(self) -> None:
        self.authenticate_as_staff_user()

        response = self.client.get(self.url, {"status": "active"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data["results"]:
            self.assertEqual(item["status"], "active")

    def test_list_invalid_status_returns_400(self) -> None:
        self.authenticate_as_staff_user()

        response = self.client.get(self.url, {"status": "invalid"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_list_search_by_email(self) -> None:
        self.authenticate_as_staff_user()

        response = self.client.get(self.url, {"search": "user@example.com"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [item["email"] for item in response.data["results"]]
        self.assertIn("user@example.com", emails)


class AdminAccountDetailTests(AdminAccountBaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url_name = "admin_account_detail"

    def test_detail_unauthenticated_returns_401(self) -> None:
        url = reverse(self.url_name, kwargs={"account_id": self.staff_user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error_detail", response.data)

    def test_detail_forbidden_for_normal_user(self) -> None:
        self.authenticate_as_normal_user()

        url = reverse(self.url_name, kwargs={"account_id": self.staff_user.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_success_for_staff(self) -> None:
        self.authenticate_as_staff_user()

        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
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

    def test_detail_not_found_for_staff(self) -> None:
        self.authenticate_as_staff_user()

        url = reverse(self.url_name, kwargs={"account_id": 9999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error_detail", response.data)


class AdminAccountUpdateTests(AdminAccountBaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url_name = "admin_account_detail"

    def test_update_unauthenticated_returns_401(self) -> None:
        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.patch(url, {"name": "변경"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_forbidden_for_normal_user(self) -> None:
        self.authenticate_as_normal_user()

        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.patch(url, {"name": "변경"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_success_for_staff(self) -> None:
        self.authenticate_as_staff_user()

        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        payload = {
            "nickname": "renickname",
            "name": "변경된 이름",
            "phone_number": "01099999999",
            "gender": "M",
            "status": "inactive",
            "profile_img_url": "https://example.com/new.png",
        }

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        for field in [
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "status",
            "profile_img_url",
            "updated_at",
        ]:
            self.assertIn(field, data)

        self.assertEqual(data["nickname"], "renickname")
        self.assertEqual(data["name"], "변경된 이름")
        self.assertEqual(data["phone_number"], "01099999999")
        self.assertEqual(data["status"], "inactive")

    def test_update_invalid_phone_returns_400(self) -> None:
        self.authenticate_as_staff_user()

        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.patch(
            url,
            {"phone_number": "010-1234-5678"},  # 잘못된 포맷
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)
        self.assertIn("phone_number", response.data["error_detail"])

    def test_update_phone_conflict_returns_409(self) -> None:
        self.authenticate_as_staff_user()

        other = User.objects.create(
            email="other@example.com",
            password="password123",
            name="다른유저",
            nickname="other",
            phone_number="01088888888",
            gender="F",
            birthday=date(2001, 1, 1),
            profile_img_url="https://example.com/other.png",
            is_active=True,
        )

        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.patch(
            url,
            {"phone_number": other.phone_number},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error_detail", response.data)


class AdminAccountDeleteTests(AdminAccountBaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url_name = "admin_account_detail"

    def test_delete_unauthenticated_returns_401(self) -> None:
        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_forbidden_for_staff(self) -> None:
        self.authenticate_as_staff_user()

        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_success_for_superuser(self) -> None:
        self.authenticate_as_super_user()

        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"],
            f"유저 데이터가 삭제되었습니다. - pk: {self.normal_user.id}",
        )
        self.assertFalse(User.objects.filter(id=self.normal_user.id).exists())

    def test_delete_not_found_returns_404(self) -> None:
        self.authenticate_as_super_user()

        url = reverse(self.url_name, kwargs={"account_id": 9999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminAccountRoleUpdateTests(AdminAccountBaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.url_name = "admin_account_role_update"

    def test_role_update_unauthenticated_returns_401(self) -> None:
        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.patch(url, {"role": "staff"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_role_update_forbidden_for_staff(self) -> None:
        self.authenticate_as_staff_user()

        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.patch(url, {"role": "staff"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_role_update_success_for_superuser(self) -> None:
        self.authenticate_as_super_user()

        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.patch(url, {"role": "staff"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "권한이 변경되었습니다.")

        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.is_staff)
        self.assertFalse(self.normal_user.is_superuser)

    def test_role_update_invalid_role_returns_400(self) -> None:
        self.authenticate_as_super_user()

        url = reverse(self.url_name, kwargs={"account_id": self.normal_user.id})
        response = self.client.patch(url, {"role": "invalid"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error_detail", response.data)

    def test_role_update_not_found_returns_404(self) -> None:
        self.authenticate_as_super_user()

        url = reverse(self.url_name, kwargs={"account_id": 9999})
        response = self.client.patch(url, {"role": "staff"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
