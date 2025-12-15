from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models.users import User


class TestUserLoginAPI(APITestCase):
    def setUp(self) -> None:
        self.url = "/api/v1/accounts/login/"
        self.active_user = User.objects.create_user(
            email="active@example.com", password="validpassword123", is_active=True
        )
        self.active_data = {"email": "active@example.com", "password": "validpassword123"}
        self.inactive_user = User.objects.create_user(
            email="inactive@example.com", password="inactivepassword123", is_active=False
        )
        self.inactive_data = {"email": "inactive@example.com", "password": "inactivepassword123"}

    def test_login_success(self) -> None:
        response = self.client.post(self.url, self.active_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)

    def test_login_fail_invalid_password(self) -> None:
        invalid_data = {"email": "active@example.com", "password": "wrongpassword"}
        response = self.client.post(self.url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "이메일 또는 비밀번호가 일치하지 않습니다.")

    def test_login_fail_email_not_exists(self) -> None:
        non_existent_data = {"email": "nonexistent@example.com", "password": "anypassword"}
        response = self.client.post(self.url, non_existent_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "이메일 또는 비밀번호가 일치하지 않습니다.")

    def test_login_fail_missing_field(self) -> None:
        missing_data = {"email": "active@example.com"}
        response = self.client.post(self.url, missing_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "이메일 또는 비밀번호가 일치하지 않습니다.")
