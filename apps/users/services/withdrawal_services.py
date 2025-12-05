from typing import Any

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.users.models import User, Withdrawal


def withdraw_service(user: User, withdrawal_data: dict[str, Any]) -> Withdrawal:
    if not user.is_active:
        raise ValidationError("이미 탈퇴 처리된 유저 입니다. 다시 로그인 하시면 계정 복구를 진행하실 수 있습니다.")
    with transaction.atomic():
        withdrawal = Withdrawal.objects.create(user=user, **withdrawal_data)
        user.is_active = False
        user.save()

    return withdrawal
