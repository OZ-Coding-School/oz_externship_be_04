from typing import Any
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers.oauth_serializers import SocialLoginSerializer
from apps.users.services.oauth_services import SocialLoginService


class SocialLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = SocialLoginService()
        user, is_new_user = service.login_or_signup(
            provider=serializer.validated_data["provider"],
            user_info=serializer.validated_data,
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "회원가입 성공" if is_new_user else "로그인 성공",
                "is_new_user": is_new_user,
                "user_id": user.id,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )