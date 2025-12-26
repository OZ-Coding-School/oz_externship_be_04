from typing import Any

from rest_framework import permissions
from rest_framework.request import Request


class StaffOrSuperUser(permissions.BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user

        if not user.is_authenticated:
            return False

        return user.is_staff or user.is_superuser


class SuperUserOnly(permissions.BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        user = request.user

        if not user.is_authenticated:
            return False

        return bool(user.is_superuser)
