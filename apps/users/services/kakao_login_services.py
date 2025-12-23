from typing import Any

import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError

from apps.core.logger.logging import get_logger

logger = get_logger(__name__)


class KaKaoLoginServices(object):

    def get_kakao_access_token(self, code: str) -> str:
        url = "https://kauth.kakao.com/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
        data = {
            "grant_type": "authorization_code",
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "client_id": settings.KAKAO_CLIENT_ID,
            "code": code,
        }

        logger.info(f"카카오 토큰 요청 시작: code={code}")

        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)

            logger.info(f"카카오 토큰 응답 수신: {response.status_code}")

            token_data = response.json()

            if response.status_code != 200 or "error" in token_data:
                logger.error(f"카카오 토큰 발급 실패: {token_data}")
                raise ValidationError(f"카카오 토큰 발급 실패: {token_data}")

            return str(token_data.get("access_token"))

        except requests.exceptions.Timeout:
            logger.error("카카오 토큰 요청 타임아웃")
            raise ValidationError("카카오 서버 응답 시간이 초과되었습니다.")
        except Exception as e:
            logger.error(
                f"카카오 토큰 요청 중 에러 발생: {e}",
            )
            raise e

    def get_kakao_user_info(self, token_id: str) -> dict[str, Any]:
        url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {token_id}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        }
        logger.info("카카오 유저 정보 조회 시작")

        response = requests.get(url, headers=headers, timeout=10)

        logger.info(f"카카오 유저 정보 응답 수신: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"카카오 유저 정보 조회 실패 {response.text}")
            raise ValidationError("카카오 유저 정보 조회 실패")

        response_json = response.json()

        kakao_account = response_json.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        provider_id = str(response_json.get("id"))
        email = kakao_account.get("email")
        nickname = profile.get("nickname")
        name = kakao_account.get("name")
        profile_img_url = profile.get("profile_image_url")

        birthyear = kakao_account.get("birthyear", "2000")
        birthday = kakao_account.get("birthday")
        final_birthday = f"{birthyear}-{birthday[:2]}-{birthday[2:]}"

        gender = kakao_account.get("gender")
        if gender == "male":
            gender = gender.replace("male", "M")
        elif gender == "female":
            gender = gender.replace("female", "F")

        phone_number = kakao_account.get("phone_number")
        if phone_number:
            clean_num = phone_number.replace(" ", "").replace("-", "")
            if clean_num.startswith("+82"):
                phone_number = clean_num.replace("+82", "0")
            else:
                phone_number = clean_num.replace("+", "")

        return {
            "provider_id": provider_id,
            "email": email,
            "nickname": nickname,
            "gender": gender,
            "birthday": final_birthday,
            "profile_img_url": profile_img_url,
            "name": name,
            "phone_number": phone_number,
        }
