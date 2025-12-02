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
        if obj.is_active:
            return "active"
        else:
            if obj.withdrawals.exists():
                return "withdrew"
            else:
                return "inactive"

class AdminAccountDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    nickname = serializers.CharField()
    name = serializers.CharField()
    phone_number = serializers.CharField()
    birthday = serializers.DateField(format="%Y-%m-%d")
    gender = serializers.ChoiceField(choices=("M", "F"))
    status = serializers.ChoiceField(choices=("active", "inactive", "withdrew"))
    role = serializers.ChoiceField(choices=("user", "staff", "admin"))
    profile_img_url = serializers.URLField()
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%f%z")