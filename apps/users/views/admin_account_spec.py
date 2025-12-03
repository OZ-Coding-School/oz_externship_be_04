from datetime import date, datetime, timezone
from typing import Any

from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
)
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.admin_account import (
    AdminAccountDetailSerializer,
    AdminAccountSerializer,
)
from apps.users.utils.permissions import StaffOrSuperUser


class AdminAccountListSpec(APIView):
    """
    Spec API 어드민 페이지 회원 목록 조회 -> mock 데이터입니다.
    """

    permission_classes = [StaffOrSuperUser]
    pagination_class = PageNumberPagination

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원 목록 조회 Spec",
        description="어드민 페이지 회원 목록 조회용 Spec API입니다.",
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
                name="q",
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

        user1 = User(
            id=1,
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
        user1.created_at = datetime(2025, 11, 25, 13, 0, tzinfo=timezone.utc)
        user1.status_value = "active"
        user1.withdraw_at = None  # type: ignore[attr-defined]

        user2 = User(
            id=2,
            email="user2@example.com",
            nickname="user2",
            name="박이준",
            birthday=date(2007, 12, 25),
            is_active=True,
            is_staff=True,
            is_superuser=False,
            phone_number="010111112222",
            gender="M",
            profile_img_url="https://example.com/profile/user2.png",
        )
        user2.created_at = datetime(2024, 2, 24, 17, 0, tzinfo=timezone.utc)
        user2.status_value = "active"
        user2.withdraw_at = None  # type: ignore[attr-defined]

        user3 = User(
            id=3,
            email="user3@example.com",
            nickname="user3",
            name="머대용",
            birthday=date(2001, 9, 2),
            is_active=False,
            is_staff=False,
            is_superuser=False,
            phone_number="01033334444",
            gender="F",
            profile_img_url="https://example.com/profile/user3.png",
        )
        user3.created_at = datetime(2021, 3, 9, 10, 0, tzinfo=timezone.utc)
        user3.status_value = "withdrew"
        user3.withdraw_at = datetime(2025, 12, 1, 10, 56, 505250, tzinfo=timezone.utc)  # type: ignore[attr-defined]

        accounts = [user1, user2, user3]

        params = request.query_params

        q = params.get("q")
        """검색 (아메일 or 닉네임 or 이름)"""
        if q:
            q_lower = q.lower()
            accounts = [
                u
                for u in accounts
                if q_lower in u.email.lower() or q_lower in u.nickname.lower() or q_lower in u.name.lower()
            ]

        role = params.get("role")
        """권한별 확인 (admin, staff, superuser)"""
        if role == "admin":
            accounts = [u for u in accounts if u.is_superuser]
        elif role == "staff":
            accounts = [u for u in accounts if u.is_staff and not u.is_superuser]
        elif role == "user":
            accounts = [u for u in accounts if not u.is_staff and not u.is_superuser]

        status_param = params.get("status")
        """회원 상태별 확인 (active, inactive, withdrew)"""
        if status_param:
            accounts = [u for u in accounts if u.status_value == status_param]

        paginator = self.pagination_class()
        page: list[User] | None = paginator.paginate_queryset(
            accounts,  # type: ignore[arg-type]
            request,
            view=self,
        )
        if page is None:
            page = []

        serializer = AdminAccountSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminAccountDetailSpec(APIView):
    """
    Spec API 어드민 페이지 회원 정보 상세 조회 -> mock 데이터입니다.
    """

    permission_classes = [StaffOrSuperUser]

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원 정보 상세 조회 Spec",
        description="어드민 페이지 회원 정보 상세 조회용 Spec API입니다.",
        responses={
            200: AdminAccountDetailSerializer,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
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

        serializer = AdminAccountDetailSerializer(user)
        return Response(serializer.data)
