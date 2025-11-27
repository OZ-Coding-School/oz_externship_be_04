from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.users.serializers.oauth_serializers import SocialLoginRequestSerializer
from apps.users.oauth.kakao import KakaoOAuthService


class KakaoLoginView(APIView):
    def post(self, request):
        serializer = SocialLoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]
        kakao_service = KakaoOAuthService()

        try:
            access_token = kakao_service.get_access_token(
                code,
                client_id="KAKAO_CLIENT_ID_PLACEHOLDER",
                redirect_uri="REDIRECT_URI_PLACEHOLDER",
            )
            user_info = kakao_service.get_user_info(access_token)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "카카오 인증 성공", "user_info": user_info},
            status=status.HTTP_200_OK,
        )
