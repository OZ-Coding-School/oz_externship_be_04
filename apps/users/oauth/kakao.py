import requests

class KakaoOAuthService:
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"

    def get_access_token(self, code, client_id, redirect_uri):
        data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        response = requests.post(self.TOKEN_URL, data=data)
        response.raise_for_status()
        return response.json().get("access_token")

    def get_user_info(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USER_INFO_URL, headers=headers)
        response.raise_for_status()
        data = response.json()

        kakao_account = data.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        return {
            "provider_id": data.get("id"),
            "nickname": profile.get("nickname"),
            "profile_image": profile.get("profile_image_url"),
        }
