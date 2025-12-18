from typing import Any
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class SocialLoginTests(APITestCase):

    def test_kakao_login_url(self) -> None:
        try:
            url = reverse("kakao_login")
        except:
            url = "/api/v1/accounts/social-login/kakao"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("login_url", response.data)

    def test_naver_login_url(self) -> None:
        try:
            url = reverse("naver_login")
        except:
            url = "/api/v1/accounts/social-login/naver"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("login_url", response.data)

    @patch("apps.users.services.kakao_login_services.KaKaoLoginServices.get_kakao_access_token")
    @patch("apps.users.services.kakao_login_services.KaKaoLoginServices.get_kakao_user_info")
    def test_kakao_callback_success(self, mock_get_user_info: Any, mock_get_token: Any) -> None:

        mock_get_token.return_value = "fake_kakao_access_token"
        mock_get_user_info.return_value = {
            "provider_id": "1k2a3k4a5o",
            "email": "kakaotest@kakao.com",
            "nickname": "kakaonick",
            "name": "테스트",
            "gender": "M",
            "birthday": "1990-01-01",
            "profile_img_url": "http://kakao-image.com/profile.png",
            "phone_number": "01012345678",
        }

        try:
            url = reverse("kakao_callback")
        except:
            url = "/api/v1/accounts/social-login/kakao/callback"

        response = self.client.get(url, {"code": "fake_code"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertEqual(response.data["provider"], "kakao")
        self.assertEqual(response.data["email"], "kakaotest@kakao.com")

    @patch("apps.users.services.naver_login_services.NaverLoginService.get_naver_access_token")
    @patch("apps.users.services.naver_login_services.NaverLoginService.get_naver_user_info")
    def test_naver_callback_success(self, mock_get_user_info: Any, mock_get_token: Any) -> None:

        mock_get_token.return_value = "fake_naver_access_token"
        mock_get_user_info.return_value = {
            "provider_id": "n1a2v3e4r",
            "email": "navertest@naver.com",
            "nickname": "navernick",
            "name": "네이버버",
            "gender": "F",
            "birthday": "1995-12-25",
            "profile_img_url": "http://naver-image.com/profile.jpg",
            "phone_number": "01077778888",
        }

        try:
            url = reverse("naver_callback")
        except:
            url = "/api/v1/accounts/social-login/naver/callback"

        response = self.client.get(url, {"code": "random_code", "state": "random_state"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertEqual(response.data["provider"], "naver")
        self.assertEqual(response.data["email"], "navertest@naver.com")
