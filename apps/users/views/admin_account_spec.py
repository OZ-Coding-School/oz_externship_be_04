from datetime import date, datetime, timezone

from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.admin_account import AdminAccountSerializer
from apps.users.utils.pagination import Pageable, offset_paginate_list
from apps.users.utils.permissions import StaffOrSuperUser


class AdminAccountListSpec(APIView):
    """
    Spec API 어드민 페이지 회원 목록 조회 API -> mock 데이터입니다.
    """

    permission_classes = [StaffOrSuperUser]

    def get(self, request, *args, **kwargs):

        user1 = User(
            id=1,
            email="user1@example.com",
            nickname="user1",
            name="홍승우",
            birthday=date(2005, 1, 1),
            is_active=True,
            is_staff=True,
            is_superuser=True,
            phone_number="01012345678",
            gender="M",
            profile_image_url="http://example.com/user1.png",
        )
        user1.created_at = datetime(2025, 11, 25, 13, 0, tzinfo=timezone.utc)
        user1.status_value = "ACTIVE"
        user1.withdrawal_requested_at = None

        user2 = User(
            id=2,
            email="user2@example.com",
            nickname="user2",
            name="박이준",
            birthday=date(2007, 12, 25),
            is_active=False,
            is_staff=True,
            is_superuser=True,
            phone_number="010111112222",
            gender="M",
            profile_image_url="http://example.com/user2.png",
        )
        user2.created_at = datetime(2024, 2, 24, 17, 0, tzinfo=timezone.utc)
        user2.status_value = "INACTIVE"
        user2.withdrawal_requested_at = None

        user3 = User(
            id=3,
            email="user3@example.com",
            nickname="user3",
            name="머대용",
            birthday=date(2001, 9, 2),
            is_active=True,
            is_staff=False,
            is_superuser=False,
            phone_number="01033334444",
            gender="F",
            profile_image_url="http://example.com/user3.png",
        )
        user3.created_at = datetime(2021, 3, 9, 10, 0, tzinfo=timezone.utc)
        user3.status_value = "WITHDRAWING"
        user3.withdrawal_requested_at = None

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
        if role == "ADMIN":
            accounts = [u for u in accounts if u.is_superuser]
        elif role == "STAFF":
            accounts = [u for u in accounts if u.is_staff and not u.is_superuser]
        elif role == "USER":
            accounts = [u for u in accounts if not u.is_staff and not u.is_superuser]

        status_param = params.get("status")
        """회원 상태별 확인 (active, inactive, withdrawal)"""
        if status_param:
            accounts = [u for u in accounts if getattr(u, "status_value", None) == status_param]

        pageable = Pageable(
            page=params.get("page", 1),
            size=params.get("size", 10),
        )
        page_obj = offset_paginate_list(accounts, pageable)

        serializer = AdminAccountSerializer(page_obj.items, many=True)

        response_data = {
            "count": page_obj.total_count,
            "page": page_obj.current_page,
            "size": page_obj.size,
            "total_count": page_obj.total_pages,
            "has_next": page_obj.has_next,
            "has_prev": page_obj.has_prev,
            "results": serializer.data,
        }
        return Response(response_data)
