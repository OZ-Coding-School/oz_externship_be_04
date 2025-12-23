import secrets

from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models.users import User


class PasswordManagementIntegrationTestCase(APITestCase):
    def setUp(self) -> None:
        cache.clear()

        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="OldPass1234!@",
            name="홍길동",
            nickname="테스터",
            phone_number="01012345678",
            gender="M",
        )

        self.valid_token = secrets.token_hex(32)
        cache.set(f"reset_token:{self.valid_token}", self.user.email, timeout=1800)

    def tearDown(self) -> None:
        cache.clear()
        User.objects.all().delete()

    def test_post_password_reset_success(self) -> None:
        url = "/api/v1/accounts/find-password"
        data = {"token": self.valid_token, "new_password": "NewPass1234!@"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "비밀번호 변경 성공.")

        self.user.refresh_from_db()
        self.assertTrue(check_password("NewPass1234!@", self.user.password))

        self.assertIsNone(cache.get(f"reset_token:{self.valid_token}"))

    def test_post_password_reset_invalid_token(self) -> None:
        url = "/api/v1/accounts/find-password"
        data = {"token": "invalid_token_12345", "new_password": "NewPass1234!@"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "유효하지 않거나 만료된 토큰입니다.")

    def test_post_password_reset_weak_password(self) -> None:
        url = "/api/v1/accounts/find-password"
        data = {"token": self.valid_token, "new_password": "12345678"}  # 숫자만

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data["error_detail"])

    def test_post_password_reset_token_reuse_prevented(self) -> None:
        url = "/api/v1/accounts/find-password"
        data = {"token": self.valid_token, "new_password": "NewPass1234!@"}

        response1 = self.client.post(url, data, format="json")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(url, data, format="json")
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_change_password_success(self) -> None:
        self.client.force_authenticate(user=self.user)

        url = "/api/v1/accounts/find-password"
        data = {
            "current_password": "OldPass1234!@",
            "new_password": "NewPass1234!@",
            "confirm_password": "NewPass1234!@",
        }

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "비밀번호 변경 성공.")

        self.user.refresh_from_db()
        self.assertTrue(check_password("NewPass1234!@", self.user.password))

    def test_patch_change_password_wrong_current(self) -> None:
        self.client.force_authenticate(user=self.user)

        url = "/api/v1/accounts/find-password"
        data = {
            "current_password": "WrongPass1234!@",
            "new_password": "NewPass1234!@",
            "confirm_password": "NewPass1234!@",
        }

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_password", response.data["error_detail"])
        self.assertEqual(response.data["error_detail"]["current_password"][0], "현재 비밀번호가 일치하지 않습니다.")

    def test_patch_change_password_mismatch(self) -> None:
        self.client.force_authenticate(user=self.user)

        url = "/api/v1/accounts/find-password"
        data = {
            "current_password": "OldPass1234!@",
            "new_password": "NewPass1234!@",
            "confirm_password": "DifferentPass1234!@",
        }

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data["error_detail"])
        self.assertEqual(response.data["error_detail"]["new_password"][0], "새 비밀번호가 일치하지 않습니다.")

    def test_patch_change_password_weak(self) -> None:
        self.client.force_authenticate(user=self.user)

        url = "/api/v1/accounts/find-password"
        data = {
            "current_password": "OldPass1234!@",
            "new_password": "12345678",  # 숫자만
            "confirm_password": "12345678",
        }

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data["error_detail"])

    def test_patch_change_password_unauthorized(self) -> None:
        url = "/api/v1/accounts/find-password"
        data = {
            "current_password": "OldPass1234!@",
            "new_password": "NewPass1234!@",
            "confirm_password": "NewPass1234!@",
        }

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_email_verify_and_get_token(self) -> None:
        cache.set("email:reset_password:testuser@example.com", "ABC123", timeout=300)

        url = "/api/v1/accounts/find-password/verify-email"
        data = {"email": "testuser@example.com", "code": "ABC123"}

        response = self.client.post(url, data, format="json")

        if response.status_code != status.HTTP_200_OK:
            print(f"Error Response: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "비밀번호 찾기를 위한 이메일 인증에 성공하였습니다.")
        self.assertIn("reset_token", response.data)

        token = response.data["reset_token"]
        self.assertIsNotNone(token)
        self.assertEqual(len(token), 64)

        cached_email = cache.get(f"reset_token:{token}")
        self.assertEqual(cached_email, "testuser@example.com")

        self.assertIsNone(cache.get("email:reset_password:testuser@example.com"))
