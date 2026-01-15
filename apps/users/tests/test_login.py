from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models.users import User


class TestUserLoginAPI(APITestCase):
    def setUp(self) -> None:
        self.url = "/api/v1/accounts/login"
        self.active_user = User.objects.create(
            email="active@example.com",
            is_active=True,
            nickname="nickname1",
            name="Active User",
            gender="M",
            phone_number="01011112222",
        )
        self.active_user.set_password("validpassword123")
        self.active_user.save()
        self.active_data = {"email": "active@example.com", "password": "validpassword123"}
        self.inactive_user = User.objects.create(
            email="inactive@example.com",
            is_active=False,
            nickname="nickname12",
            name="Inactive User",
            gender="F",
            phone_number="01033334444",
        )
        self.inactive_user.set_password("inactivepassword123")
        self.inactive_user.save()
        self.inactive_data = {"email": "inactive@example.com", "password": "inactivepassword123"}

    def test_login_success(self) -> None:
        response = self.client.post(self.url, self.active_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.cookies)

    def test_token_refresh_success(self) -> None:
        login_response = self.client.post(self.url, self.active_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        refresh_url = "/api/v1/accounts/token/refresh"
        response = self.client.post(refresh_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)

    def test_token_refresh_no_cookie(self) -> None:
        refresh_url = "/api/v1/accounts/token/refresh"
        response = self.client.post(refresh_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error_detail"], "리프레시 토큰이 없습니다.")

    def test_logout_success(self) -> None:
        self.client.post(self.url, self.active_data, format="json")

        logout_url = "/api/v1/accounts/logout"
        response = self.client.post(logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "로그아웃 되었습니다.")

    def test_logout_blacklist_token(self) -> None:
        login_response = self.client.post(self.url, self.active_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        refresh_cookie = login_response.cookies.get("refresh_token")
        assert refresh_cookie is not None
        refresh_token = refresh_cookie.value

        logout_url = "/api/v1/accounts/logout"
        self.client.post(logout_url)

        self.client.cookies["refresh_token"] = refresh_token
        refresh_url = "/api/v1/accounts/token/refresh"
        response = self.client.post(refresh_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_rotation_blacklist(self) -> None:
        login_response = self.client.post(self.url, self.active_data, format="json")
        refresh_cookie = login_response.cookies.get("refresh_token")
        assert refresh_cookie is not None
        old_refresh_token = refresh_cookie.value

        refresh_url = "/api/v1/accounts/token/refresh"
        response = self.client.post(refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.cookies["refresh_token"] = old_refresh_token
        response = self.client.post(refresh_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

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
