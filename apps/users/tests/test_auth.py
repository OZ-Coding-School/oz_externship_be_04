from unittest.mock import patch  # mocking 전용 import

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class test_user_register(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.account_urls = reverse("signup")
        self.valid_user_data = {
            "email": "test@test.com",
            "password": "test_register123",
            "password_confirm": "test_register123",
            "name": "test",
            "nickname": "testtest",
            "phone_number": "01012345678",
            "gender": "M",
            "birthday": "1990-01-01",
        }

        self.patcher = patch("django.core.cache.cache.get")
        self.mock_cache_get = self.patcher.start()
        self.mock_cache_get.return_value = "true"
        # -------------------------------

    def tearDown(self) -> None:
        self.patcher.stop()

        User.objects.all().delete()

    def test_success_register(self) -> None:
        before = User.objects.count()

        response = self.client.post(self.account_urls, self.valid_user_data)
        after = User.objects.count()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(before + 1, after)
        user = User.objects.get(email=self.valid_user_data["email"])
        self.assertEqual(user.name, self.valid_user_data["name"])
        self.assertTrue(user.is_active)

    def test_field_missed(self) -> None:
        required_fields = ["email", "password", "name", "nickname", "phone_number", "gender"]
        for field in required_fields:
            with self.subTest(field=field):
                invalid_data = self.valid_user_data.copy()
                removed_value = invalid_data.pop(field)

                response = self.client.post(self.account_urls, invalid_data)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("error_detail", response.data)
                self.assertIsInstance(response.data["error_detail"], str)

    def test_email(self) -> None:
        response = self.client.post(self.account_urls, self.valid_user_data)
        second_response = self.client.post(self.account_urls, self.valid_user_data)

        self.assertEqual(second_response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error_detail", second_response.data)
        self.assertEqual(second_response.data["error_detail"], "이미 중복된 회원가입 내역이 존재합니다.")

    def test_nickname(self) -> None:
        User.objects.create_user(
            email="test2@test.com",
            password="dfgasfgseirk123",
            name="testnickname",
            nickname=self.valid_user_data["nickname"],
            phone_number="01099999999",
            gender="M",
            birthday="1990-01-01",
        )
        response = self.client.post(self.account_urls, self.valid_user_data)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error_detail", response.data)
        self.assertEqual(response.data["error_detail"], "이미 중복된 회원가입 내역이 존재합니다.")

    def test_phone_number(self) -> None:
        User.objects.create_user(
            email="other@test.com",
            password="gsprelpo123",
            name="testphone",
            nickname="testphone",
            phone_number=self.valid_user_data["phone_number"],
            gender="M",
            birthday="1990-01-01",
        )
        response = self.client.post(self.account_urls, self.valid_user_data)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("error_detail", response.data)
        self.assertEqual(response.data["error_detail"], "이미 중복된 회원가입 내역이 존재합니다.")

    def test_invalid_phone_number(self) -> None:
        invaild_phone_number = [
            "1234567890",
            "010 1234 5678",
            "0101234567",
            "010123456789",
            "abc12345678",
            "02012345678",
            "010-abcd-5678",
            "010--1234-5678",
        ]
        for phone_number in invaild_phone_number:
            with self.subTest(phone_number=phone_number):
                valid_data = self.valid_user_data.copy()
                valid_data["phone_number"] = phone_number
                response = self.client.post(self.account_urls, valid_data)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("error_detail", response.data)
                self.assertIsInstance(response.data["error_detail"], str)

    def test_valid_phone_number(self) -> None:
        valid_phone_number = [
            ("01023456789", "user1", "test1@test.com"),
            ("010-1934-5678", "user2", "test2@test.com"),
            ("01112345678", "user3", "test3@test.com"),
            ("011-1234-5679", "user4", "test4@test.com"),
        ]

        for phone_number, nickname, email in valid_phone_number:
            with self.subTest(phone_number=phone_number):
                valid_data = self.valid_user_data.copy()
                valid_data["phone_number"] = phone_number
                valid_data["nickname"] = nickname
                valid_data["email"] = email

                response = self.client.post(self.account_urls, valid_data, format="json")

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertIn("detail", response.data)
