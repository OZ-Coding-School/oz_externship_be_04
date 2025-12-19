import uuid
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models.social_user import ProviderChoices
from apps.users.services.kakao_login_services import KaKaoLoginServices
from apps.users.services.naver_login_services import NaverLoginService
from apps.users.services.oauth_services import SocialLoginService


class NaverLoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="네이버 로그인",
        description="현재 네이버 로그인 된 유저의 상세 정보를 조회합니다.",
        methods=["GET"],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request: Request) -> Response:

        state = uuid.uuid4().hex

        login_url = (
            f"https://nid.naver.com/oauth2.0/authorize?response_type=code"
            f"&client_id={settings.NAVER_CLIENT_ID}"
            f"&redirect_uri={settings.NAVER_REDIRECT_URI}"
            f"&state={state}"
        )
        return Response({"login_url": login_url})


class NaverCallBackView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="네이버 로그인 콜백",
        description="네이버 인증 코드를 받아 처리합니다.",
        methods=["GET"],
        responses={302: None},
    )
    def get(self, request: Request) -> HttpResponse:
        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code or not state:
            return Response({"error_detail": "네이버 로그인 인증에 실패했습니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            naver_login = NaverLoginService()
            access_token = naver_login.get_naver_access_token(code, state)
            user_info = naver_login.get_naver_user_info(access_token)

            social_service = SocialLoginService()
            user, is_created = social_service.login_or_signup(provider=ProviderChoices.NAVER, user_info=user_info)

            token = RefreshToken.for_user(user)

            return_list = urlencode(
                {
                    "access_token": str(token.access_token),
                    "is_created": is_created,
                    "email": user.email,
                    "nickname": user.nickname,
                    "name": user.name,
                    "phone_number": user.phone_number,
                    "birthday": user.birthday,
                    "gender": user.gender,
                    "profile_img_url": user.profile_img_url or "",
                    "provider": "naver",
                }
            )

            base_url = getattr(settings, "FRONTEND_BASE_URL", "http://127.0.0.1:8000")
            redirect_url = f"{base_url}/social-callback?{return_list}"

            response = redirect(redirect_url)

            response.set_cookie(
                key="refresh_token",
                value=str(token),
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=7 * 24 * 60 * 60,
            )
            return response

        except:
            return Response(
                {"error_detail": "네이버 로그인 도중 오류가 발생했습니다."}, status=status.HTTP_400_BAD_REQUEST
            )


class KakaoLoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="카카오 로그인",
        description="현재 카카오 로그인 된 유저의 상세 정보를 조회합니다.",
        methods=["GET"],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request: Request) -> Response:
        login_url = (
            f"https://kauth.kakao.com/oauth/authorize?response_type=code"
            f"&client_id={settings.KAKAO_CLIENT_ID}"
            f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        )
        return Response({"login_url": login_url})


class KakaoCallBackView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="카카오 로그인 콜백",
        description="카카오 인증 코드를 받아 처리합니다.",
        methods=["GET"],
        responses={302: None},
    )
    def get(self, request: Request) -> HttpResponse:
        code = request.GET.get("code")

        if not code:
            return Response({"error_detail": "카카오 로그인 인증에 실패했습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            kakao_login = KaKaoLoginServices()
            access_token = kakao_login.get_kakao_access_token(code)
            user_info = kakao_login.get_kakao_user_info(access_token)
            social_service = SocialLoginService()
            user, is_created = social_service.login_or_signup(
                provider=ProviderChoices.KAKAO,
                user_info=user_info,
            )

            token = RefreshToken.for_user(user)

            return_list = urlencode(
                {
                    "access_token": str(token.access_token),
                    "is_created": is_created,
                    "email": user.email,
                    "name": user.name,
                    "nickname": user.nickname,
                    "phone_number": user.phone_number,
                    "birthday": user.birthday,
                    "gender": user.gender,
                    "profile_img_url": user.profile_img_url or "",
                    "provider": "kakao",
                }
            )

            base_url = getattr(settings, "FRONTEND_BASE_URL", "http://127.0.0.1:8000")
            redirect_url = f"{base_url}/social-callback?{return_list}"

            response = redirect(redirect_url)
            response.set_cookie(
                key="refresh_token",
                value=str(token),
                httponly=True,
                secure=False,
                samesite="Lax",
                max_age=7 * 24 * 60 * 60,
            )
            return response

        except:
            return Response(
                {"error_detail": "카카오 로그인 도중 오류가 발생했습니다."}, status=status.HTTP_400_BAD_REQUEST
            )
