from typing import Any

import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError


class NaverLoginService:

    def get_naver_access_token(self, code: str, state: str) -> str:
        url = "https://nid.naver.com/oauth2.0/token"
        params = {
            "client_id": settings.NAVER_CLIENT_ID,
            "client_secret": settings.NAVER_CLIENT_SECRET,
            "redirect_uri": settings.NAVER_REDIRECT_URI,
            "grant_type": "authorization_code",
            "state": state,
            "code": code,
        }

        response = requests.get(url, params=params)
        token_data = response.json()

        if response.status_code != 200 or "error" in token_data:
            raise ValidationError(f"네이버 토큰 발급 실패: {token_data}")

        return str(token_data.get("access_token"))

    def get_naver_user_info(self, token_id: str) -> dict[str, Any]:
        url = "https://openapi.naver.com/v1/nid/me"
        headers = {"Authorization": f"Bearer {token_id}"}

        response = requests.get(url, headers=headers)
        if not response.status_code == 200:
            raise ValidationError("네이버 유저 정보 조회 실패")

        response_json = response.json()

        if not response_json.get("resultcode") == "00":
            raise ValidationError("네이버 유저 정보 호출 실패")

        user_data = response_json.get("response", {})

        birthyear = user_data.get("birthyear")
        birthday = user_data.get("birthday")
        final_birthday = None
        if birthyear and birthday:
            final_birthday = f"{birthyear}-{birthday}"

        gender = user_data.get("gender")
        final_gender = None
        if gender in ["M", "F"]:
            final_gender = gender

        phone_number = user_data.get("mobile")
        if phone_number:
            phone_number = phone_number.replace("-", "")

        return {
            "email": user_data.get("email"),
            "nickname": user_data.get("nickname"),
            "name": user_data.get("name"),
            "phone_number": phone_number,
            "birthday": final_birthday,
            "gender": final_gender,
            "profile_img_url": user_data.get("profile_image"),
            "provider_id": user_data.get("id"),
        }
