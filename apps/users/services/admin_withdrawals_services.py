from typing import Any, Optional, cast

from django.db.models import Q
from rest_framework.exceptions import NotFound

from apps.core.pagination import OffsetPage, Pageable, offset_paginate_queryset
from apps.users.models.withdrawal import Withdrawal
from apps.users.utils.consts import WithdrawalReason


def get_admin_withdrawal_list(
    pageable: Pageable,
    search: Optional[str],
    role_param: Optional[str],
    sort_param: Optional[str],
    reason_param: Optional[str],
) -> OffsetPage[Withdrawal]:
    """
    어드민 회원 탈퇴 목록 조회 서비스 함수
    """
    qs = Withdrawal.objects.select_related("user").all()

    if search:
        search_filter = Q()

        if search.isdigit():
            search_filter |= Q(id=int(search))

        search_filter |= Q(user__email__icontains=search)
        search_filter |= Q(user__nickname__icontains=search)
        search_filter |= Q(user__name__icontains=search)

        qs = qs.filter(search_filter)

    if role_param in {"admin", "staff", "user"}:
        if role_param == "admin":
            qs = qs.filter(user__is_superuser=True)
        elif role_param == "staff":
            qs = qs.filter(user__is_staff=True, user__is_superuser=False)
        else:
            qs = qs.filter(user__is_staff=False, user__is_superuser=False)

    if reason_param:
        allowed_reasons = {choices[0] for choices in WithdrawalReason.choices}
        if reason_param in allowed_reasons:
            qs = qs.filter(reason=reason_param)

    if sort_param == "latest":
        qs = qs.order_by("-withdrawn_at", "-id")
    elif sort_param == "oldest":
        qs = qs.order_by("withdrawn_at", "id")
    else:
        qs = qs.order_by("id")

    page = offset_paginate_queryset(cast(Any, qs), pageable)
    return cast(OffsetPage[Withdrawal], page)


def get_admin_withdrawal_detail(withdrawal_id: int) -> Withdrawal:
    """
    어드민 회원 탈퇴 정보 상세 조회 서비스 함수
    """
    withdrawal = Withdrawal.objects.select_related("user").filter(pk=withdrawal_id, user__isnull=False).first()

    if withdrawal is None:
        raise NotFound(detail={"error_detail": "회원탈퇴 정보를 찾을 수 없습니다."})

    return withdrawal
