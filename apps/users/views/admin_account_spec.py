from datetime import date, datetime, timezone
from typing import Any

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
)
from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import Pageable, offset_paginate_list
from apps.users.models import User
from apps.users.serializers.admin_account import AdminAccountSerializer
from apps.users.utils.permissions import StaffOrSuperUser


class AdminAccountListResponseSerializer(serializers.Serializer[Any]):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    result = AdminAccountSerializer(many=True)


class ErrorResponseSerializer(serializers.Serializer[Any]):
    """
    {
        "error_detail": str,
    }
    """

    error_detail = serializers.CharField()


class AdminAccountListSpec(APIView):
    """
    Spec API 어드민 페이지 회원 목록 조회 API -> mock 데이터입니다.
    """

    permission_classes = [StaffOrSuperUser]

    @extend_schema(
        tags=["V1"],
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
            ),
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                location="query",
                description="상세 필터 (active, inactive, withdrew)",
            ),
        ],
        responses={
            200: AdminAccountListResponseSerializer(),
            401: ErrorResponseSerializer(),
            403: ErrorResponseSerializer(),
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
                value={"error_detail: 자격 인증 데이터가 제공되지 않았습니다."},
                status_codes=["401"],
            ),
            OpenApiExample(
                name="Forbidden Example",
                value={"error_detail: 권한이 없습니다."},
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

        params = request.query_params

        pageable = Pageable.from_params(
            page_raw=params.get("page"),
            size_raw=params.get("page_size"),
        )

        page_obj = offset_paginate_list(accounts, pageable)

        serializer = AdminAccountSerializer(page_obj.items, many=True)

        base_url = request.build_absolute_uri(request.path)
        current_page = page_obj.current_page
        page_size = page_obj.size

        def build_page_url(page: int) -> str:
            query_params = params.copy()
            query_params["page"] = str(page)
            query_params["page_size"] = str(page_size)
            return f"{base_url}?{query_params.urlencode()}"

        if page_obj.has_next:
            next_url: str | None = build_page_url(current_page + 1)
        else:
            next_url = None

        if page_obj.has_prev:
            previous_url: str | None = build_page_url(current_page - 1)
        else:
            previous_url = None

        response_data = {
            "count": page_obj.total_count,
            "next": next_url,
            "previous": previous_url,
            "results": serializer.data,
        }

        return Response(response_data)
