from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

User = get_user_model()

class test_user_register(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('signup')
        self.valid_user_data = {
            "email": "test@test.com",
            "password": "test_register123",
            "password_confirm": "test_register123",
            "name": "test",
            "nickname": "testtest",
            "phone_number": "01012345678",
            "gender": "M",
            "birthday": "1990-01-01",
            "profile_img_url": "https://example.com/profile.jpg"
        }

    def tearDown(self):
        User.objects.all().delete()

    def test_success_register(self):
        before = User.objects.count()
        print("before", before)

        response = self.client.post(self.signup_url, self.valid_user_data)
        after = User.objects.count()
        print("after", after)
        print("status_code", response.status_code)
        print("response.data", response.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(before + 1, after)
        user = User.objects.get(email=self.valid_user_data['email'])
        self.assertEqual(user.name, self.valid_user_data['name'])
        self.assertFalse(user.is_active)

    def test_field_missed(self):
        required_fields = ['email', 'password', 'name', 'nickname', 'phone_number', 'gender']
        for field in required_fields:
            with self.subTest(field=field):
                invalid_data = self.valid_user_data.copy()
                removed_value = invalid_data.pop(field)
                print("removed_value", removed_value)
                response = self.client.post(self.signup_url, invalid_data)
                print("status_code", response.status_code)
                print("response.data", response.data)

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(field, response.data)

    def test_email(self):
        response = self.client.post(self.signup_url, self.valid_user_data)
        print("response status", response.status_code)
        second_response = self.client.post(self.signup_url, self.valid_user_data)
        print("second_response status", second_response.status_code)

        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', second_response.data)

    def test_nickname(self):
        User.objects.create_user(
            email='test2@test.com',
            password='dfgasfgseirk123',
            name='testnickname',
            nickname=self.valid_user_data['nickname'],
            phone_number='01012345678',
            gender='M',
            birthday='1990-01-01',
        )
        print("test nickname", self.valid_user_data['nickname'])
        response = self.client.post(self.signup_url, self.valid_user_data)
        print("status_code", response.status_code)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nickname', response.data)

    def test_phone_number(self):
        User.objects.create_user(
            email='other@test.com',
            password='gsprelpo123',
            name='testphone',
            nickname='testphone',
            phone_number=self.valid_user_data['phone_number'],
            gender='M',
            birthday='1990-01-01',
        )
        print("test_phone_number", self.valid_user_data['phone_number'])
        response = self.client.post(self.signup_url, self.valid_user_data)
        print("status_code", response.status_code)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)
