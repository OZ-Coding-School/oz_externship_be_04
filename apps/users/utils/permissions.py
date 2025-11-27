from rest_framework import permissions


class StaffOrSuperUser(permissions.BasePermission):
    """
    관리자(staff or superuser) 로그인만 허용합니다.
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
