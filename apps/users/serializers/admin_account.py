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
        if obj.is_superuser:
            return "Admin"
        if obj.is_staff:
            return "Staff"
        return "User"

    def get_status(self, obj: User) -> str:
        status_value: Optional[str] = obj.status_value

        if status_value is not None:
            return status_value
        if obj.is_active:
            return "Active"
        return "Inactive"
