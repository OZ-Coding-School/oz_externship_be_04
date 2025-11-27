from typing import Optional

from rest_framework import serializers

from apps.users.models import User


class AdminAccountSerializer(serializers.ModelSerializer[User]):
    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    joined_at = serializers.DateTimeField(source="created_at", read_only=True)
    withdrawal_requested_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "birthday",
            "role",
            "status",
            "joined_at",
            "withdrawal_requested_at",
        ]

    def get_role(self, obj: User) -> str:
        if getattr(obj, "is_superuser", False):
            return "Admin"
        if getattr(obj, "is_staff", False):
            return "Staff"
        return "USER"

    def get_status(self, obj: User) -> str:
        status: Optional[str] = getattr(obj, "status_value", None)
        if status is not None:
            return status
        if getattr(obj, "is_active", False):
            return "Active"
        return "Inactive"
