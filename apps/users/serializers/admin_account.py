from rest_framework import serializers

from apps.users.models import User


class AdminAccountSerializer(serializers.ModelSerializer[User]):
    """
    어드민 회원 목록 조회용 serializer
    """

    role = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    withdraw_at = serializers.SerializerMethodField()

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

    def get_withdraw_at(self, obj: User):
        withdrawal = obj.withdrawals.order_by("-created_at").first()
        if withdrawal is None:
            return None
        return withdrawal.created_at


class AdminAccountDetailSerializer(serializers.ModelSerializer[User]):
    """
    어드민 회원 정보 상세 조회용 serializer
    """

    role = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "gender",
            "nickname",
            "birthday",
            "phone_number",
            "email",
            "role",
            "status",
            "created_at",
            "profile_img_url",
        ]
