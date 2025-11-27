from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.oauth.kakao import KakaoOAuthService
from apps.users.serializers.oauth_serializers import (
    SocialLoginRequestSerializer,
    UserInfoSerializer,
)
from apps.users.services.oauth_services import SocialLoginService

class KakaoLoginView(APIView):
    def post(self, request):
        serializer = SocialLoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"]

        kakao_service = KakaoOAuthService()

        try:
            access_token = kakao_service.get_access_token(
                code=code,
                client_id=settings.KAKAO_CLIENT_ID,
                redirect_uri=settings.KAKAO_REDIRECT_URI,
            )

            user_info = kakao_service.get_user_info(access_token)

        except Exception as e:
            return Response(
                {"detail": f"Kakao OAuth 통신 중 오류가 발생했습니다: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = SocialLoginService.get_or_create_user(
            provider="kakao",
            provider_id=user_info["provider_id"],
            nickname=user_info.get("nickname"),
            profile_img_url=user_info.get("profile_image"),
        )

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        user_data = UserInfoSerializer(user).data

        return Response(
            {
                "access": str(access),
                "refresh": str(refresh),
                "user": user_data,
                "is_new": created,
            },
            status=status.HTTP_200_OK,
        )