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
            "profile_img_url": "https://example.com/profile.jpg",
        }

    def tearDown(self) -> None:
        User.objects.all().delete()

    def test_success_register(self) -> None:
        before = User.objects.count()

        response = self.client.post(self.account_urls, self.valid_user_data)
        after = User.objects.count()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(before + 1, after)
        user = User.objects.get(email=self.valid_user_data["email"])
        self.assertEqual(user.name, self.valid_user_data["name"])
        self.assertFalse(user.is_active)

    def test_field_missed(self) -> None:
        required_fields = ["email", "password", "name", "nickname", "phone_number", "gender"]
        for field in required_fields:
            with self.subTest(field=field):
                invalid_data = self.valid_user_data.copy()
                removed_value = invalid_data.pop(field)

                response = self.client.post(self.account_urls, invalid_data)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

    def test_email(self) -> None:
        response = self.client.post(self.account_urls, self.valid_user_data)
        second_response = self.client.post(self.account_urls, self.valid_user_data)

        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", second_response.data)

    def test_nickname(self) -> None:
        User.objects.create_user(
            email="test2@test.com",
            password="dfgasfgseirk123",
            name="testnickname",
            nickname=self.valid_user_data["nickname"],
            phone_number="01012345678",
            gender="M",
            birthday="1990-01-01",
        )
        response = self.client.post(self.account_urls, self.valid_user_data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("nickname", response.data)

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

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data)

    def test_invalid_phone_number(self) -> None:
        invaild_phone_number = [
            "1234567890",  # 앞자리 누락
            "010 1234 5678",  # 공백
            "0101234567",  # 10자리
            "010123456789",  # 12자리
            "abc12345678",  # 문자 포함
            "02012345678",  # 020
            "010-abcd-5678",  # 하이픈 문자포함
            "010--1234-5678",  # 하이픈 중복
        ]
        for phone_number in invaild_phone_number:
            with self.subTest(phone_number=phone_number):
                valid_data = self.valid_user_data.copy()
                valid_data["phone_number"] = phone_number
                response = self.client.post(self.account_urls, valid_data)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("phone_number", response.data)

    def test_valid_phone_number(self) -> None:
        valid_phone_number = [
            ("01023456789", "user1", "test1@test.com"),  # 하이픈 없음
            ("010-1934-5678", "user2", "test2@test.com"),  # 하이픈 포함
            ("01112345678", "user3", "test3@test.com"),  # 011 하이픈 없음
            ("011-1234-5679", "user4", "test4@test.com"),  # 011 하이픈 포함
        ]

        for phone_number, nickname, email in valid_phone_number:
            with self.subTest(phone_number=phone_number):
                valid_data = self.valid_user_data.copy()
                valid_data["phone_number"] = phone_number
                valid_data["nickname"] = nickname
                valid_data["email"] = email

                response = self.client.post(self.account_urls, valid_data, format="json")

                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertIn("phone_number", response.data)
