import uuid

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.logger.logging import get_logger
from apps.users.models.social_user import ProviderChoices
from apps.users.services.kakao_login_services import KaKaoLoginServices
from apps.users.services.naver_login_services import NaverLoginService
from apps.users.services.oauth_services import SocialLoginService

check_secure = not settings.DEBUG
check_samesite = "None" if not settings.DEBUG else "Lax"
check_domain = ".ozcoding.site" if not settings.DEBUG else None

logger = get_logger(__name__)


class NaverLoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="네이버 로그인",
        description="현재 네이버 로그인 된 유저의 상세 정보를 조회합니다.",
        methods=["GET"],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request: Request) -> HttpResponse:

        state = uuid.uuid4().hex

        login_url = (
            f"https://nid.naver.com/oauth2.0/authorize?response_type=code"
            f"&client_id={settings.NAVER_CLIENT_ID}"
            f"&redirect_uri={settings.NAVER_REDIRECT_URI}"
            f"&state={state}"
        )
        return redirect(login_url)


class NaverCallBackView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="네이버 로그인 콜백",
        description="네이버 인증 코드를 받아 리다이렉트 시킵니다.",
        methods=["GET"],
        responses={302: None},
    )
    def get(self, request: Request) -> HttpResponse:
        code = request.GET.get("code")
        state = request.GET.get("state")

        base_url = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173")
        if not code or not state:
            logger.error("네이버 인증 코드 or 상태값 오류")
            return redirect(f"{base_url}/social-callback?error_code=NAVER_ERROR_001")

        try:
            naver_login = NaverLoginService()
            naver_auth_token = naver_login.get_naver_access_token(code, state)
            user_info = naver_login.get_naver_user_info(naver_auth_token)

            social_service = SocialLoginService()
            user, is_created = social_service.login_or_signup(provider=ProviderChoices.NAVER, user_info=user_info)

            naver_token = RefreshToken.for_user(user)
            jwt_access_token = str(naver_token.access_token)
            jwt_refresh_token = str(naver_token)

            base_url = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173")
            redirect_url = f"{base_url}/social-callback"
            response = redirect(redirect_url)

            response.set_cookie(
                key="access_token",
                value=jwt_access_token,
                httponly=False,
                secure=check_secure,
                samesite=check_samesite,  # type: ignore
                domain=check_domain,
                max_age=3600,
            )

            response.set_cookie(
                key="refresh_token",
                value=jwt_refresh_token,
                httponly=True,
                secure=check_secure,
                samesite=check_samesite,  # type: ignore
                domain=check_domain,
                max_age=7 * 24 * 60 * 60,
            )
            return response

        except ValidationError as e:
            logger.error(f"네이버 검증 에러 {e}")
            return redirect(f"{base_url}/social-callback?error_code=NAVER_ERROR_001")

        except Exception as e:
            logger.error(f"네이버 시스템 에러 {e}")
            return redirect(f"{base_url}/social-callback?error_code=NAVER_ERROR_002")


class KakaoLoginView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="카카오 로그인",
        description="현재 카카오 로그인 된 유저의 상세 정보를 조회합니다.",
        methods=["GET"],
        responses={200: OpenApiTypes.OBJECT},
    )
    def get(self, request: Request) -> HttpResponse:
        login_url = (
            f"https://kauth.kakao.com/oauth/authorize?response_type=code"
            f"&client_id={settings.KAKAO_CLIENT_ID}"
            f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
        )
        return redirect(login_url)


class KakaoCallBackView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Account"],
        summary="카카오 로그인 콜백",
        description="카카오 인증 코드를 받아 리다이렉트 시킵니다.",
        methods=["GET"],
        responses={302: None},
    )
    def get(self, request: Request) -> HttpResponse:
        code = request.GET.get("code")

        base_url = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173")
        if not code:
            logger.error(f"카카오 인증 코드 오류")
            return redirect(f"{base_url}/social-callback?error_code=KAKAO_ERROR_001")

        try:
            kakao_login = KaKaoLoginServices()
            kakao_auth_token = kakao_login.get_kakao_access_token(code)
            user_info = kakao_login.get_kakao_user_info(kakao_auth_token)
            social_service = SocialLoginService()
            user, is_created = social_service.login_or_signup(
                provider=ProviderChoices.KAKAO,
                user_info=user_info,
            )

            kakao_token = RefreshToken.for_user(user)
            jwt_access_token = str(kakao_token.access_token)
            jwt_refresh_token = str(kakao_token)

            base_url = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173")
            redirect_url = f"{base_url}/social-callback"
            response = redirect(redirect_url)

            response.set_cookie(
                key="access_token",
                value=jwt_access_token,
                httponly=False,
                secure=check_secure,
                samesite=check_samesite,  # type: ignore
                domain=check_domain,
                max_age=3600,
            )

            response.set_cookie(
                key="refresh_token",
                value=jwt_refresh_token,
                httponly=True,
                secure=check_secure,
                samesite=check_samesite,  # type: ignore
                domain=check_domain,
                max_age=7 * 24 * 60 * 60,
            )
            return response

        except ValidationError as e:
            logger.error(f"카카오 검증 에러 {e}")
            return redirect(f"{base_url}/social-callback?error_code=KAKAO_ERROR_001")

        except Exception as e:
            logger.error(f"카카오 시스템 에러 {e}")
            return redirect(f"{base_url}/social-callback?error_code=KAKAO_ERROR_002")
