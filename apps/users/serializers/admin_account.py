from typing import Optional

from rest_framework import serializers

from apps.users.models import User


class AdminAccountSerializer(serializers.ModelSerializer[User]):
    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    withdraw_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "birthday",
            "status",
            "role",
            "withdraw_at",
            "created_at",
        ]

    def get_role(self, obj: User) -> str:
        if obj.is_superuser:
            return "admin"
        if obj.is_staff:
            return "staff"
        return "user"

    def get_status(self, obj: User) -> str:
        status_value: Optional[str] = obj.status_value

        if status_value is not None:
            return status_value
        if obj.is_active:
            return "active"
        return "inactive"
