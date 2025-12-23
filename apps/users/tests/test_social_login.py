from typing import Any
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.services.kakao_login_services import KaKaoLoginServices
from apps.users.services.naver_login_services import NaverLoginService


class SocialLoginTests(APITestCase):

    def test_kakao_login_url(self) -> None:
        try:
            url = reverse("kakao_login")
        except:
            url = "/api/v1/accounts/social-login/kakao"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("kauth.kakao.com", response.url)  # type: ignore

    def test_naver_login_url(self) -> None:
        try:
            url = reverse("naver_login")
        except:
            url = "/api/v1/accounts/social-login/naver"

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("nid.naver.com", response.url)  # type: ignore

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

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)

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

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)


class OAuthServiceTests(TestCase):

    @patch("requests.post")
    def test_kakao_get_token_success(self, mock_post: Any) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "fake_access_token"}
        mock_post.return_value = mock_response

        service = KaKaoLoginServices()
        token = service.get_kakao_access_token("fake_code")

        self.assertEqual(token, "fake_access_token")

    @patch("requests.get")
    def test_kakao_get_user_info_success(self, mock_get: Any) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123456789,
            "kakao_account": {
                "email": "test@kakao.com",
                "birthyear": "1995",
                "birthday": "1225",
                "gender": "male",
                "phone_number": "+82 10-1234-5678",
                "profile": {"nickname": "kakaonick", "profile_image_url": "http://kakao-image.com/profile.png"},
            },
        }
        mock_get.return_value = mock_response

        service = KaKaoLoginServices()
        user_info = service.get_kakao_user_info("fake_token")

        self.assertEqual(user_info["email"], "test@kakao.com")
        self.assertEqual(user_info["birthday"], "1995-12-25")
        self.assertEqual(user_info["phone_number"], "01012345678")
        self.assertEqual(user_info["gender"], "M")

    @patch("requests.get")
    def test_naver_get_token_success(self, mock_get: Any) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "fake_naver_token"}
        mock_get.return_value = mock_response

        service = NaverLoginService()
        token = service.get_naver_access_token("fake_code", "fake_state")

        self.assertEqual(token, "fake_naver_token")

    @patch("requests.get")
    def test_naver_get_user_info_success(self, mock_get: Any) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resultcode": "00",
            "response": {
                "id": "naver_id_123",
                "email": "test@naver.com",
                "nickname": "navernick",
                "name": "네이버버",
                "mobile": "010-9876-5432",
                "birthyear": "1990",
                "birthday": "01-01",
                "gender": "F",
                "profile_image": "http://naver-image.com/profile.jpg",
            },
        }
        mock_get.return_value = mock_response

        service = NaverLoginService()
        user_info = service.get_naver_user_info("fake_token")
        self.assertEqual(user_info["email"], "test@naver.com")
        self.assertEqual(user_info["birthday"], "1990-01-01")
        self.assertEqual(user_info["phone_number"], "01098765432")
        self.assertEqual(user_info["gender"], "F")
