from typing import Optional

from django.db.models import Q, QuerySet

from apps.core.pagination import OffsetPage, Pageable, offset_paginate_queryset
from apps.users.models.withdrawal import Withdrawal
from apps.users.utils.reason_choices import WithdrawalReason


def get_admin_withdrawal_list(
    pageable: Pageable,
    search: Optional[str],
    role_parm: Optional[str],
    sort_parm: Optional[str],
    reason_parm: Optional[str],
) -> OffsetPage[Withdrawal]:

    qs: QuerySet[Withdrawal] = Withdrawal.objects.select_related("user").all()

    qs = qs.order_by("id")

    if search:
        search_filter = Q()

        if search.isdigit():
            search_filter |= Q(id=int(search))

        search_filter |= Q(user_email__icontains=search)
        search_filter |= Q(user_nickname__icontains=search)
        search_filter |= Q(user_name__icontains=search)

        qs = qs.filter(search_filter)

    if role_parm in {"admin", "staff", "user"}:
        if role_parm == "admin":
            qs = qs.filter(user__is_superuser=True)
        elif role_parm == "staff":
            qs = qs.filter(user__is_staff=True, user__is_superuser=False)
        else:
            qs = qs.filter(user__is_staff=False, user__is_superuser=False)

    if reason_parm:
        allowed_reasons = {choices[0] for choices in WithdrawalReason.choices}
        if reason_parm in allowed_reasons:
            qs = qs.filter(reason=reason_parm)

    if sort_parm == "lastest":
        qs = qs.order_by("-withdrawn_at", "-id")
    elif sort_parm == "oldest":
        qs = qs.order_by("-withdrawn_at", "id")

    page: OffsetPage[Withdrawal] = offset_paginate_queryset(qs, pageable)
    return page
