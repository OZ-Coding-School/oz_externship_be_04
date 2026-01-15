from typing import Any, Optional

from rest_framework import serializers

from apps.users.models import User
from apps.users.models.withdrawal import Withdrawal
from apps.users.utils.consts import WithdrawalReason


class AdminWithdrawalListItemSerializer(serializers.Serializer[Any]):
    """
    어드민 페이지의 회원 탈퇴 내역 목록에 개별 탈퇴 항목 한 건을 나타낼 때 사용하는 Serializer
    """

    id = serializers.IntegerField()
    email = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    birthday = serializers.SerializerMethodField()
    reason = serializers.ChoiceField(choices=WithdrawalReason.choices)
    withdrawn_at = serializers.DateTimeField()

    def get_email(self, obj: Withdrawal) -> Optional[str]:
        user: Optional[User] = obj.user
        if user is None:
            return None
        return user.email

    def get_name(self, obj: Withdrawal) -> Optional[str]:
        user: Optional[User] = obj.user
        if user is None:
            return None
        return user.name

    def get_role(self, obj: Withdrawal) -> Optional[str]:
        user: Optional[User] = obj.user
        if user is None:
            return None
        return user.role

    def get_birthday(self, obj: Withdrawal) -> Optional[str]:
        user: Optional[User] = obj.user
        if user is None or user.birthday is None:
            return None
        return user.birthday.isoformat()


class AdminWithdrawalUserDetailsSerializer(serializers.ModelSerializer[User]):
    """
    어드민 탈퇴 상세 조회에서 탈퇴 내역에 연결된 User 정보를 중첩 형태로 보여줄 때 사용하는 Serializer
    """

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "nickname",
            "name",
            "gender",
            "role",
            "status",
            "profile_img_url",
            "created_at",
        ]

    def to_representation(self, instance: User) -> dict[str, Any]:
        data = super().to_representation(instance)
        if not data.get("profile_img_url"):
            data["profile_img_url"] = None
        return data


class AdminWithdrawalDetailSerializer(serializers.ModelSerializer[Withdrawal]):
    """
    어드민 페이지 회원 탈퇴 상세 조회 API에서 사용하는 Serializer
    """

    user = AdminWithdrawalUserDetailsSerializer(read_only=True)

    class Meta:
        model = Withdrawal
        fields = [
            "id",
            "user",
            "reason",
            "reason_detail",
            "due_date",
            "withdrawn_at",
        ]
