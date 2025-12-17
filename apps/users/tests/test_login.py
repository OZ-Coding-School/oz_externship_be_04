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
        # 리프레시 토큰 쿠키 확인
        self.assertIn("refresh_token", response.cookies)

    def test_token_refresh_success(self) -> None:
        """토큰 재발급 성공 테스트"""
        # 먼저 로그인
        login_response = self.client.post(self.url, self.active_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # 쿠키가 설정된 상태에서 토큰 재발급
        refresh_url = "/api/v1/accounts/token/refresh"
        response = self.client.post(refresh_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)

    def test_token_refresh_no_cookie(self) -> None:
        """리프레시 토큰 쿠키 없이 재발급 시도"""
        refresh_url = "/api/v1/accounts/token/refresh"
        response = self.client.post(refresh_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error_detail"], "리프레시 토큰이 없습니다.")

    def test_logout_success(self) -> None:
        """로그아웃 성공 테스트"""
        # 먼저 로그인
        self.client.post(self.url, self.active_data, format="json")

        # 로그아웃
        logout_url = "/api/v1/accounts/logout"
        response = self.client.post(logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "로그아웃 되었습니다.")

    def test_logout_blacklist_token(self) -> None:
        """로그아웃 후 블랙리스트된 토큰으로 재발급 시도 시 실패"""
        # 로그인
        login_response = self.client.post(self.url, self.active_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # refresh_token 저장
        refresh_cookie = login_response.cookies.get("refresh_token")
        assert refresh_cookie is not None
        refresh_token = refresh_cookie.value

        # 로그아웃 (토큰 블랙리스트)
        logout_url = "/api/v1/accounts/logout"
        self.client.post(logout_url)

        # 블랙리스트된 토큰으로 재발급 시도
        self.client.cookies["refresh_token"] = refresh_token
        refresh_url = "/api/v1/accounts/token/refresh"
        response = self.client.post(refresh_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_rotation_blacklist(self) -> None:
        """토큰 재발급 시 이전 refresh 토큰이 블랙리스트 처리되는지 확인"""
        # 로그인
        login_response = self.client.post(self.url, self.active_data, format="json")
        refresh_cookie = login_response.cookies.get("refresh_token")
        assert refresh_cookie is not None
        old_refresh_token = refresh_cookie.value

        # 첫 번째 재발급 (성공)
        refresh_url = "/api/v1/accounts/token/refresh"
        response = self.client.post(refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 이전 토큰으로 다시 재발급 시도 (실패해야 함)
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
