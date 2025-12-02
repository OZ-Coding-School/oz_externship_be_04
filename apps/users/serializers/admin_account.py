from rest_framework import serializers

from apps.users.models import User


class AdminAccountSerializer(serializers.ModelSerializer[User]):
    """
    어드민 회원 목록 조회용 serializer
    """
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
        if obj.is_active:
            return "active"
        else:
            if obj.withdrawals.exists():
                return "withdrew"
            else:
                return "inactive"

class AdminAccountDetailSerializer(serializers.ModelSerializer[User]):
    """
    어드민 회원 정보 상세 조회용 serializer
    """
    role = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "phone_number",
            "birthday",
            "gender",
            "status",
            "role",
            "profile_img_url",
            "created_at",
        ]

        def get_role(self, obj: User) -> str:
            if obj.is_superuser:
                return "admin"
            if obj.is_staff:
                return "staff"
            return "user"

        def get_status(self, obj: User) -> str:
            if obj.is_active:
                return "active"
            else:
                if obj.withdrawals.exists():
                    return "withdrew"
                else:
                    return "inactive"