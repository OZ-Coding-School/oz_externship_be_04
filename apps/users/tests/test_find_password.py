from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models.users import User


class PasswordResetTestCase(APITestCase):
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

    def tearDown(self) -> None:
        cache.clear()
        User.objects.all().delete()

    def test_find_password_success(self) -> None:
        cache.set("email_verified:find_password:testuser@example.com", True, timeout=300)

        url = "/api/v1/accounts/find-password"
        data = {"email": "testuser@example.com", "new_password": "NewPass1234!@"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "비밀번호 변경 성공.")

        self.user.refresh_from_db()
        self.assertTrue(check_password("NewPass1234!@", self.user.password))

    def test_find_password_not_verified(self) -> None:
        url = "/api/v1/accounts/find-password"
        data = {"email": "testuser@example.com", "new_password": "NewPass1234!@"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error_detail"], "이메일 인증이 완료되지 않았습니다.")
