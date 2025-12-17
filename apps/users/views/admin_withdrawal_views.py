from typing import Any, Optional

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
from apps.users.serializers.admin_withdrawal_serializers import (
    AdminWithdrawalDetailSerializer,
    AdminWithdrawalListItemSerializer,
)
from apps.users.services.admin_withdrawal_services import (
    get_admin_withdrawal_detail,
    get_admin_withdrawal_list,
)
from apps.users.utils.permissions import StaffOrSuperUser
from apps.users.utils.reason_choices import WithdrawalReason

AdminWithdrawalSimpleErrorSerializer = inline_serializer(
    name="AdminWithdrawalSimpleError",
    fields={"error_detail": serializers.CharField()},
)


class AdminWithdrawalList(APIView):
    """
    어드민 페이지 회원 탈퇴 내역 목록 조회 APIView
    """

    permission_classes = [StaffOrSuperUser]
    pagination_class = PageNumberPagination

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원 탈퇴 목록 조회",
        description="스태프 및 관리자 권한을 가진 유저는 어드민 페이지 회원 탈퇴 목록을 조회할 수 있습니다.",
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location="query",
                description="페이지 번호 / 기본값 : 1",
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location="query",
                description="페이지 당 개수 / 기본값 : 10",
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location="query",
                description="검색기준 (pk, 이메일, 닉네임, 이름)",
            ),
            OpenApiParameter(
                name="role",
                type=OpenApiTypes.STR,
                location="query",
                description="권한별 필터링(user, staff, admin)",
                enum=["user", "staff", "admin"],
            ),
            OpenApiParameter(
                name="sort",
                type=OpenApiTypes.STR,
                location="query",
                description="정렬 기준(latest: 최신순, oldest: 오래된 순)",
                enum=["latest", "oldest"],
            ),
            OpenApiParameter(
                name="reason",
                type=OpenApiTypes.STR,
                location="query",
                description="탈퇴 사유별 필터링",
                enum=[choice[0] for choice in WithdrawalReason],
            ),
        ],
        responses={
            200: AdminWithdrawalListItemSerializer,
            401: AdminWithdrawalSimpleErrorSerializer,
            403: AdminWithdrawalSimpleErrorSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success Example",
                value={
                    "count": 1973,
                    "next": "http://api.ozcoding.site/api/v1/admin/withdrawals?page=2",
                    "previous": None,
                    "results": [
                        {
                            "id": 2025,
                            "email": "wanthome@test.com",
                            "name": "박재현",
                            "role": "user",
                            "birthday": "2001-09-07",
                            "reason": "NO_LONGER_NEEDED",
                            "withdrawn_at": "2025-12-16T01:01:30+09:00",
                        }
                    ],
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
        ],
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        params = request.query_params

        pageable = Pageable.from_params(
            page_raw=params.get("page"),
            size_raw=params.get("page_size"),
        )

        search: Optional[str] = params.get("search")
        role_param: Optional[str] = params.get("role")
        sort_param: Optional[str] = params.get("sort")
        reason_param: Optional[str] = params.get("reason")

        page = get_admin_withdrawal_list(
            pageable=pageable,
            search=search,
            role_param=role_param,
            sort_param=sort_param,
            reason_param=reason_param,
        )

        serializer = AdminWithdrawalListItemSerializer(page.items, many=True)

        base_url = request.build_absolute_uri(request.path)

        def build_page_url(page_number: int) -> str:
            query_params = params.copy()
            query_params["page"] = str(page_number)
            query_params["page_size"] = str(page.size)
            return f"{base_url}?{query_params.urlencode()}"

        next_url = build_page_url(page.current_page + 1) if page.has_next else None
        previous_url = build_page_url(page.current_page - 1) if page.has_prev else None

        response_data = {
            "count": page.total_count,
            "next": next_url,
            "previous": previous_url,
            "results": serializer.data,
        }

        return Response(response_data)


class AdminWithdrawalDetail(APIView):
    """
    어드민 페이지 회원 탈퇴 내역 상세 조회 API View
    """

    permission_classes = [StaffOrSuperUser]

    @extend_schema(
        tags=["Admin"],
        summary="어드민 페이지 회원 탈퇴 상세 내역 조회",
        description="스태프 및 관리자 권한을 가진 유저는 어드민 페이지 내에서 회원 탈퇴 상세 정보를 조회할 수 있습니다.",
        responses={
            200: AdminWithdrawalDetailSerializer,
            401: AdminWithdrawalSimpleErrorSerializer,
            403: AdminWithdrawalSimpleErrorSerializer,
            404: AdminWithdrawalSimpleErrorSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success Example",
                value={
                    "id": 1,
                    "user": {
                        "id": 1,
                        "email": "user@example.com",
                        "nickname": "test",
                        "name": "홍길동",
                        "gender": "M",
                        "role": "user",
                        "status": "active",
                        "profile_img_url": "https://example.com/images/profiles/image.png",
                        "created_at": "2025-10-30T14:01:57.505250+09:00",
                    },
                    "reason": "NO_LONGER_NEEDED",
                    "reason_detail": "이제 안써요.",
                    "due_date": "2025-11-01",
                    "withdrawn_at": "2025-11-01T01:01:30+09:00",
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
                name="Not Found Example",
                value={"error_detail": "회원탈퇴 정보를 찾을 수 없습니다."},
                status_codes=["404"],
            ),
        ],
    )
    def get(self, request: Request, withdrawal_id: int, *args: Any, **kwargs: Any) -> Response:
        withdrawal = get_admin_withdrawal_detail(withdrawal_id=withdrawal_id)
        serializer = AdminWithdrawalDetailSerializer(withdrawal)
        return Response(serializer.data)
