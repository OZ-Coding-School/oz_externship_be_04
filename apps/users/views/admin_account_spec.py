from datetime import date, datetime, timezone
from typing import Any

from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import Pageable
from apps.users.models import User
from apps.users.serializers.admin_serializers import (
    AdminAccountDetailReadSerializer,
    AdminAccountDetailSerializer,
    AdminAccountRoleUpdateSerializer,
    AdminAccountSerializer,
    AdminAccountUpdateSerializer,
)
from apps.users.services.admin_services import get_admin_account_list
from apps.users.utils.permissions import StaffOrSuperUser, SuperUserOnly

AdminAccountUpdate400ErrorSerializer = inline_serializer(
    name="AdminAccountUpdate400Error",
    fields={
        "error_detail": serializers.DictField(
            child=serializers.ListField(
                child=serializers.CharField(),
            )
        )
    },
)

AdminAccountUpdateSimpleErrorSerializer = inline_serializer(
    name="AdminAccountUpdateSimpleError",
    fields={
        "error_detail": serializers.CharField(),
    },
)

AdminAccountDeleteSuccessSerializer = inline_serializer(
    name="AdminAccountDeleteSuccessSerializer",
    fields={
        "detail": serializers.CharField(help_text="삭제 시 성공 메시지"),
    },
)

AdminAccountRoleUpdateSuccessSerializer = inline_serializer(
    name="AdminAccountRoleUpdateSuccess",
    fields={
        "detail": serializers.CharField(help_text="권한 변경 성공 메시지"),
    },
)


class AdminAccountListSpec(APIView):
    """
    어드민 페이지 회원 목록 조회 APIView
    """

    permission_classes = [StaffOrSuperUser]
    pagination_class = PageNumberPagination

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원 목록 조회",
        description="어드민 페이지 회원 목록 조회용 API입니다.",
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location="query",
                description="페이지 번호 / 기본값: 1",
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location="query",
                description="페이지 당 개수 / 기본값: 10",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location="query",
                description="검색 (이메일, 닉네임, 이름)",
            ),
            OpenApiParameter(
                name="role",
                type=OpenApiTypes.STR,
                location="query",
                description="권한 필터 (user, staff, admin)",
                enum=["user", "staff", "admin"],
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location="query",
                description="상세 필터 (active, inactive, withdrew)",
                enum=["active", "inactive", "withdrew"],
            ),
        ],
        responses={
            200: AdminAccountSerializer,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                name="Success Example",
                value={
                    "count": 4018,
                    "next": "http://api.ozcoding.site/api/v1/admin/accounts?page=1&page_size=10",
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "email": "user@example.com",
                            "nickname": "string",
                            "name": "string",
                            "birthday": "2025-11-20",
                            "status": "active",
                            "role": "user",
                            "withdraw_at": "2025-10-30T14:01:57.505250+09:00",
                            "created_at": "2025-10-30T14:01:57.505250+09:00",
                        }
                    ],
                },
            ),
            OpenApiExample(
                name="Unauthorized Example",
                value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status_codes=["401"],
            ),
            OpenApiExample(
                name="Forbidden Example",
                value={"error_detail": "권한이 없습니다."},
                status_codes=["403"],
            ),
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:

        params = request.query_params

        pageable = Pageable.from_params(
            page_raw=params.get("page"),
            size_raw=params.get("page_size"),
        )

        status_param = params.get("status")
        role_param = params.get("role")
        search = params.get("search")

        page = get_admin_account_list(
            pageable=pageable,
            status_param=status_param,
            role_param=role_param,
            search=search,
        )

        serializer = AdminAccountSerializer(page.items, many=True)

        base_url = request.build_absolute_uri(request.path)

        def build_page_url(page_number: int) -> str:
            query_params = params.copy()
            query_params["page"] = str(page_number)
            query_params["page_size"] = str(page.size)
            return f"{base_url}?{query_params.urlencode()}"

        next_url = build_page_url(page.current_page + 1) if page.has_next else None
        previous_url = build_page_url(page.current_page - 1) if page.has_prev else None

        response_date = {
            "count": page.total_count,
            "next": next_url,
            "previous": previous_url,
            "results": serializer.data,
        }

        return Response(response_date)


class AdminAccountDetailSpec(APIView):
    """
    Spec API 어드민 페이지 회원 정보 상세 조회 -> mock 데이터입니다.
    """

    permission_classes = [StaffOrSuperUser]

    def get_permissions(self) -> list[Any]:
        """
        유저 정보 상세 조회 및 유저 정보 수정 -> StaffOrSuperUser.
        유저 정보 삭제 -> SuperUserOnly
        """
        if self.request.method == "DELETE":
            return [SuperUserOnly()]
        return [perm() for perm in self.permission_classes]

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원 정보 상세 조회 Spec",
        description="어드민 페이지 회원 정보 상세 조회용 Spec API입니다.",
        responses={
            200: AdminAccountDetailReadSerializer,
            401: AdminAccountUpdateSimpleErrorSerializer,
            403: AdminAccountUpdateSimpleErrorSerializer,
            404: AdminAccountUpdateSimpleErrorSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success Example",
                value={
                    "id": 1,
                    "name": "홍승우",
                    "gender": "M",
                    "nickname": "user1",
                    "birthday": "2005-01-01",
                    "phone_number": "01012345678",
                    "email": "user1@example.com",
                    "role": "user",
                    "status": "active",
                    "created_at": "2005-01-01T13:00:47.50525+09:00",
                    "profile_img_url": "https://example.com/profile/user1.png",
                },
                status_codes=["200"],
            ),
            OpenApiExample(
                name="Unauthorized Example",
                value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status_codes=["401"],
            ),
            OpenApiExample(
                name="Forbidden Example",
                value={"error_detail": "권한이 없습니다."},
                status_codes=["403"],
            ),
            OpenApiExample(
                name="Notfound Example",
                value={"error_detail": "사용자 정보를 찾을 수 없습니다."},
                status_codes=["404"],
            ),
        ],
    )
    def get(self, request: Request, account_id: int, *args: Any, **kwargs: Any) -> Response:

        if account_id != 1:
            raise Http404

        user = User(
            id=account_id,
            email="user1@example.com",
            nickname="user1",
            name="홍승우",
            birthday=date(2005, 1, 1),
            is_active=True,
            is_staff=False,
            is_superuser=False,
            phone_number="01012345678",
            gender="M",
            profile_img_url="https://example.com/profile/user1.png",
        )
        user.created_at = datetime(2005, 1, 1, 13, 00, 47, 50525, tzinfo=timezone.utc)

        serializer = AdminAccountDetailReadSerializer(user)
        return Response(serializer.data)

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원 정보 수정 Spec",
        description=(
            "스태프 및 관리자 권한을 가진 유저는 어드민 페이지 내에서 "
            "특정 회원에 대한 정보를 수정할 수 있습니다.\n\n"
            "- 수정 가능 항목: 이름, 성별, 닉네임, 전화번호, 상태, 프로필 이미지\n"
            "- 회원 정보 상세 조회 모달 내의 '수정하기' 버튼을 통해 호출되는 API입니다."
        ),
        request=AdminAccountUpdateSerializer,
        responses={
            200: AdminAccountDetailSerializer,
            400: AdminAccountUpdate400ErrorSerializer,
            401: AdminAccountUpdateSimpleErrorSerializer,
            403: AdminAccountUpdateSimpleErrorSerializer,
            404: AdminAccountUpdateSimpleErrorSerializer,
            409: AdminAccountUpdateSimpleErrorSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success Example",
                value={
                    "id": 1,
                    "name": "홍승우",
                    "gender": "M",
                    "nickname": "updated_user1",
                    "birthday": "2005-01-01",
                    "phone_number": "01000000001",
                    "email": "user1@example.com",
                    "role": "user",
                    "is_active": True,
                    "created_at": "2005-01-01T13:00:47.50525+09:00",
                    "updated_at": "2025-10-30T14:01:57.505250+09:00",
                    "profile_img_url": "https://example.com/profile/user1.png",
                },
                status_codes=["200"],
            ),
            OpenApiExample(
                name="Bad Request Example",
                value={
                    "error_detail": {
                        "phone_number": [
                            "11자리 숫자로 구성해야 합니다.",
                        ]
                    }
                },
                status_codes=["400"],
            ),
            OpenApiExample(
                name="Forbidden Example",
                value={"error_detail": "권한이 없습니다."},
                status_codes=["403"],
            ),
            OpenApiExample(
                name="Not found Example",
                value={"error_detail": "사용자 정보를 찾을 수 없습니다."},
                status_codes=["404"],
            ),
            OpenApiExample(
                name="Conflict Example",
                value={"error_detail": "휴대폰 번호 중복으로 인하여 요청 처리에 실패하였습니다."},
                status_codes=["409"],
            ),
        ],
    )
    def patch(self, _request: Request, account_id: int, *_args: Any, **_kwargs: Any) -> Response:
        if account_id != 1:
            raise Http404

        user = User(
            id=account_id,
            email="user1@example.com",
            nickname="updated_user1",
            name="홍승우",
            birthday=date(2005, 1, 1),
            is_active=True,
            is_staff=False,
            is_superuser=False,
            phone_number="01099999999",
            gender="M",
            profile_img_url="https://example.com/profile/user1.png",
        )
        user.created_at = datetime(2005, 1, 1, 13, 00, 47, 50525, tzinfo=timezone.utc)
        user.updated_at = datetime(2025, 10, 30, 14, 1, 57, 505250, tzinfo=timezone.utc)

        serializer = AdminAccountDetailSerializer(user)
        return Response(serializer.data)

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원 정보 삭제 Spec",
        description="관리자 권한을 가진 유저는 어드민 페이지에서 특정 회원 정보를 삭제할 수 있습니다.",
        responses={
            200: AdminAccountDetailSerializer,
            401: AdminAccountUpdateSimpleErrorSerializer,
            403: AdminAccountUpdateSimpleErrorSerializer,
            404: AdminAccountUpdateSimpleErrorSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success Example",
                value={"detail": "유저 데이터가 삭제되었습니다. - pk: 1"},
                status_codes=["200"],
            ),
            OpenApiExample(
                name="Unauthorized Example",
                value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status_codes=["401"],
            ),
            OpenApiExample(
                name="Forbidden Example",
                value={"error_detail": "권한이 없습니다."},
                status_codes=["403"],
            ),
            OpenApiExample(
                name="Not found Example",
                value={"error_detail": "사용자 정보를 찾을 수 없습니다."},
                status_codes=["404"],
            ),
        ],
    )
    def delete(self, _request: Request, account_id: int) -> Response:
        if account_id != 1:
            raise Http404

        return Response(
            {"detail": f"유저 데이터가 삭제되었습니다. - pk: {account_id}"},
        )


class AdminAccountRoleUpdateSpec(APIView):

    permission_classes = [SuperUserOnly]

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원 권한 변경 Spec",
        description="관리자 권한을 가진 유저는 어드민 페이지에서 특정 유저의 권한을 변경할 수 있습니다.",
        request=AdminAccountRoleUpdateSerializer,
        responses={
            200: AdminAccountRoleUpdateSuccessSerializer,
            401: AdminAccountUpdateSimpleErrorSerializer,
            403: AdminAccountUpdateSimpleErrorSerializer,
            404: AdminAccountUpdateSimpleErrorSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success Example",
                value={"detail": "권한이 변경되었습니다."},
                status_codes=["200"],
            ),
            OpenApiExample(
                name="Unauthorized Example",
                value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                status_codes=["401"],
            ),
            OpenApiExample(
                name="Forbidden Example",
                value={"error_detail": "권한이 없습니다."},
                status_codes=["403"],
            ),
            OpenApiExample(
                name="Not found Example",
                value={"error_detail": "사용자 정보를 찾을 수 없습니다."},
                status_codes=["404"],
            ),
        ],
    )
    def patch(self, request: Request, account_id: int) -> Response:

        serializer_in = AdminAccountRoleUpdateSerializer(data=request.data)
        serializer_in.is_valid(raise_exception=True)

        if account_id != 1:
            raise Http404

        return Response({"detail": "권한이 변경되었습니다."})
