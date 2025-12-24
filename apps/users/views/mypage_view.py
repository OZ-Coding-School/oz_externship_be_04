from typing import Any

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    inline_serializer,
)
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers.mypage_serializers import (
    MyPageSerializer,
    WithdrawalSerializer,
)
from apps.users.services.mypage_services import (
    account_update_service,
)
from apps.users.services.withdrawal_services import withdraw_service
from apps.users.utils.conts import WithdrawalReason
from apps.users.views.auth_view import blacklist_token


class MyPageView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        tags=["Account"],
        summary="내 정보 조회",
        description="현재 로그인 된 유저의 상세 정보를 조회합니다.",
        request=MyPageSerializer,
        methods=["GET"],
        responses={200: MyPageSerializer, 401: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                response_only=True,
                name="success_case",
                summary="조회 성공",
                value={
                    "id": 1,
                    "email": "testemail@test.com",
                    "nickname": "testnick",
                    "name": "testname",
                    "phone_number": "01012345678",
                    "birthday": "2000-08-08",
                    "gender": "M",
                    "profile_img_url": "https://study-hub.s3.ap-northeast-2.amazonaws.com/uploads/users/profiles/6f1e2a4b-8d4c-4f1a-9d3b-7e2c5a1d2f3b.png",
                    "created_at": "2025-10-30T14:01:57.505250+09:00",
                    "role": "user",
                },
                status_codes=["200"],
            ),
            OpenApiExample(
                response_only=True,
                name="no_cookies",
                summary="인증 실패",
                value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status_codes=["401"],
            ),
        ],
    )
    def get(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = MyPageSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Account"],
        summary="내 정보 수정",
        description="내 정보( 프로필 사진, 이름, 닉네임, 생년월일, 성별 )를 수정합니다.",
        request=MyPageSerializer,
        methods=["PATCH"],
        responses={
            200: MyPageSerializer,
            400: OpenApiTypes.OBJECT,
            401: inline_serializer(
                name="UnauthorizedError",
                fields={"error_detail": serializers.CharField(default="자격 인증 데이터가 제공되지 않았습니다.")},
            ),
            409: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                response_only=True,
                name="success_case",
                summary="수정 성공",
                value={
                    "id": 1,
                    "email": "testemail@test.com",
                    "nickname": "testnick",
                    "name": "testname",
                    "birthday": "2000-08-08",
                    "gender": "M",
                    "profile_img_url": "https://study-hub.s3.ap-northeast-2.amazonaws.com/uploads/users/profiles/6f1e2a4b-8d4c-4f1a-9d3b-7e2c5a1d2f3b.png",
                    "updated_at": "2025-10-30T14:01:57.505250+09:00",
                    "role": "user",
                },
                status_codes=["200"],
            ),
            OpenApiExample(
                response_only=True,
                name="phone_number_format",
                summary="전화번호 형식 오류",
                value={"error_detail": {"phone_number": ["11자리 숫자로 구성된 포맷이어야 합니다."]}},
                status_codes=["400"],
            ),
            OpenApiExample(
                response_only=True,
                name="nickname_format",
                summary="닉네임 중복",
                value={"error_detail": "중복된 닉네임이 존재합니다."},
                status_codes=["409"],
            ),
        ],
    )
    def patch(self, request: Any) -> Response:
        serializer = MyPageSerializer(request.user, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            account_update_service(request.user, serializer.validated_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Account"],
        summary="회원 탈퇴",
        description="회원 탈퇴를 위한 스키마 입니다. 14일 후 영구 삭제 됩니다.",
        parameters=[
            OpenApiParameter(
                name="reason",
                description="탈퇴 사유 (객관식)",
                required=True,
                type=str,
                enum=[choice.value for choice in WithdrawalReason],  # type: ignore
            ),
            OpenApiParameter(
                name="reason_detail",
                description="상세 사유 (주관식)",
                required=True,
                type=str,
            ),
            OpenApiParameter(
                name="agree_check",
                description="동의 여부",
                required=True,
                type=bool,
            ),
        ],
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 423: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                request_only=True,
                name="success_case",
                summary="탈퇴 요청 데이터 예시",
                value={
                    "reason": "TOO_DIFFICULT",
                    "reason_detail": "탈퇴 테스트 양식 입니다.",
                    "agree_check": True,
                },
            ),
            OpenApiExample(
                response_only=True,
                name="success_response",
                summary="탈퇴 성공 응답 예시",
                value={
                    "detail": "회원 탈퇴 처리가 완료되었습니다. 14일 후 계정이 영구 삭제되며, 그전에 다시 로그인하시면 계정을 복구하실 수 있습니다."
                },
                status_codes=["200"],
            ),
            OpenApiExample(
                response_only=True,
                name="already_locked",
                summary="탈퇴 실패 예시 (이미 탈퇴함)",
                value={
                    "error_detail": {
                        "non_field_errors": [
                            "이미 탈퇴 처리된 유저 입니다. 다시 로그인 하시면 계정 복구를 진행하실 수 있습니다."
                        ]
                    }
                },
                status_codes=["423"],
            ),
        ],
    )
    def delete(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = WithdrawalSerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        data.pop("agree_check")

        withdraw_service(request.user, data)

        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                refresh = RefreshToken(refresh_token)
                blacklist_token(refresh)
            except TokenError:
                pass

        response = Response(
            {
                "detail": "회원 탈퇴 처리가 완료되었습니다. 14일 후 계정이 영구 삭제되며, 그전에 다시 로그인하시면 계정을 복구하실 수 있습니다."
            },
            status=status.HTTP_200_OK,
        )
        response.delete_cookie("refresh_token")
        return response
