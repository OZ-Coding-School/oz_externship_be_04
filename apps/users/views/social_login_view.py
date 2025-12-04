from typing import Any, Dict
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.users.serializers.oauth_serializers import SocialLoginSerializer
from apps.users.services.oauth_services import SocialLoginService


class SocialLoginView(APIView):

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        provider = serializer.validated_data["provider"]
        provider_id = serializer.validated_data["provider_id"]

        service = SocialLoginService()
        user, created = service.login_or_signup(provider, {"provider_id": provider_id})

        return Response(
            {
                "message": "회원가입 성공" if created else "로그인 성공",
                "user_id": user.id,
                "is_new_user": created,
            },
            status=status.HTTP_200_OK,
        )
