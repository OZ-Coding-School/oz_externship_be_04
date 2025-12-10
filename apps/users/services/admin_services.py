from django.db.models import Q, QuerySet
from rest_framework.exceptions import ValidationError

from apps.core.pagination import OffsetPage, Pageable, offset_paginate_queryset
from apps.users.models import User


def get_admin_account_list(
    *,
    pageable: Pageable,
    status_param: str | None = None,
    role_param: str | None = None,
    search: str | None = None,
) -> OffsetPage[User]:

    qs: QuerySet[User] = User.objects.all()

    if status_param:
        allowed_status = {"active", "inactive", "withdrawal_pending"}
        if status_param not in allowed_status:
            raise ValidationError(
                {"detail": "status 파라미터는 active, inactive, withdrawal_pending 중에서 하나여야 합니다."}
            )

        if status_param == "active":
            qs = qs.filter(is_active=True, withdrawals__isnull=True)
        elif status_param == "inactive":
            qs = qs.filter(is_active=False, withdrawals__isnull=True)
        elif status_param == "withdrawal_pending":
            qs = qs.filter(withdrawals__isnull=False).distinct()

    if role_param:
        allowed_role = {"admin", "staff", "user"}
        if role_param not in allowed_role:
            raise ValidationError({"detail": "role 파라미터는 admin, staff, user 중에서 하나여야 합니다."})

        if role_param == "admin":
            qs = qs.filter(is_superuser=True)
        elif role_param == "staff":
            qs = qs.filter(is_superuser=False, is_staff=True)
        elif role_param == "user":
            qs = qs.filter(is_superuser=False, is_staff=False)

    if search:
        qs = qs.filter(Q(email__icontains=search) | Q(nickname__icontains=search) | Q(name__icontains=search))

    qs = qs.order_by("id")

    page: OffsetPage[User] = offset_paginate_queryset(qs, pageable)
    return page
