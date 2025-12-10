from typing import Any

from django.db.models import Q, QuerySet
from rest_framework import status as drf_status
from rest_framework.exceptions import APIException, NotFound, ValidationError

from apps.core.pagination import OffsetPage, Pageable, offset_paginate_queryset
from apps.users.models import User


class PhoneNumberConflict(APIException):
    status_code = drf_status.HTTP_409_CONFLICT
    default_detail = "휴대폰 번호 중복으로 인하여 요청 처리에 실패하였습니다."
    default_code = "phone_number_conflict"


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


def get_admin_account_detail(*, account_id: int) -> User:
    user = User.objects.filter(id=account_id).first()
    if user is None:
        raise NotFound("사용자 정보를 찾을 수 없습니다.")

    return user


def update_admin_account(*, account_id: int, data: dict[str, Any]) -> User:
    user = User.objects.filter(id=account_id).first()
    if user is None:
        raise NotFound("사용자 정보를 찾을 수 없습니다.")

    if "phone_number" in data:
        phone_number = data["phone_number"]
        if phone_number is not None and User.objects.filter(phone_number=phone_number).exclude(id=account_id).exists():
            raise PhoneNumberConflict()

    if "nickname" in data:
        user.nickname = data["nickname"]

    if "name" in data:
        user.name = data["name"]

    if "phone_number" in data:
        user.phone_number = data["phone_number"]

    if "birthday" in data:
        user.birthday = data["birthday"]

    if "gender" in data:
        user.gender = data["gender"]

    if "profile_img_url" in data:
        user.profile_img_url = data["profile_img_url"]

    if "status" in data:
        status_value = data["status"]
        if status_value == "active":
            user.is_active = True
        elif status_value in ("inactive", "withdrew"):
            user.is_active = False

    user.save()
    return user


def delete_admin_account(*, account_id: int) -> None:
    user = User.objects.filter(id=account_id).first()
    if user is None:
        raise NotFound("사용자 정보를 찾을 수 없습니다.")

    user.delete()


def update_admin_account_role(*, account_id: int, role: str) -> None:

    user = User.objects.filter(id=account_id).first()
    if user is None:
        raise NotFound("사용자 정보를 찾을 수 없습니다.")

    if role == "admin":
        user.is_superuser = True
        user.is_staff = True
    if role == "staff":
        user.is_superuser = False
        user.is_staff = True
    if role == "user":
        user.is_superuser = False
        user.is_staff = False
    else:
        raise ValidationError({"detail": "role 파라미터는 admin, staff, user 중에서 하나여야 합니다."})

    user.save()
