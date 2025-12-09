from typing import Any, Dict

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers.oauth_serializers import SocialLoginSerializer
from apps.users.services.oauth_services import SocialLoginService


class SocialLoginView(APIView):
    @extend_schema(
        tags=["Auth"],
        summary="소셜 로그인 / 회원가입",
        description="카카오/네이버 로그인 시 provider/provider_id로 자동 회원가입 또는 로그인 처리됩니다.",
        request=SocialLoginSerializer,
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "access_token": {"type": "string"},
                        "refresh_token": {"type": "string"},
                        "user": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "nickname": {"type": "string"},
                                "profile_img_url": {"type": "string"},
                            },
                        },
                        "is_new_user": {"type": "boolean"},
                    },
                },
                description="로그인 또는 회원가입 성공",
            ),
            400: OpenApiResponse(description="잘못된 요청입니다."),
        },
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated = serializer.validated_data
        provider = validated["provider"]

        user_info: Dict[str, Any] = {
            "provider_id": validated["provider_id"],
            "email": validated.get("email"),
            "nickname": validated.get("nickname"),
            "profile_img_url": validated.get("profile_img_url"),
            "gender": validated.get("gender"),
            "phone_number": validated.get("phone_number"),
        }

        service = SocialLoginService()
        user, created = service.login_or_signup(provider, user_info)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "회원가입 성공" if created else "로그인 성공",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "id": user.id,
                    "nickname": user.nickname,
                    "profile_img_url": user.profile_img_url,
                },
                "is_new_user": created,
            },
            status=status.HTTP_200_OK,
        )
