from typing import Any

from rest_framework import permissions
from rest_framework.request import Request


class StaffOrSuperUser(permissions.BasePermission):
    """
    관리자(staff or superuser) 로그인만 허용합니다.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user

        if not user.is_authenticated:
            return False

        return user.is_staff or user.is_superuser
