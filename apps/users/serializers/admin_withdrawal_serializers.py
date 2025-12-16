from typing import Optional, Any

from rest_framework import serializers

from apps.users.models import User
from apps.users.models.withdrawal import Withdrawal
from apps.users.utils.reason_choices import WithdrawalReason


class AdminWithdrawalListItemSerializer(serializers.Serializer[Any]):
    id = serializers.IntegerField()
    email = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    birthday = serializers.SerializerMethodField()
    reason = serializers.ChoiceField(choices=WithdrawalReason.choices)
    withdrawn_at = serializers.DateTimeField()

    def get_user(self, obj: Withdrawal) -> Optional[User]:
        user = obj.user
        if user is None:
            return None
        return user

    def get_email(self, obj: Withdrawal) -> Optional[str]:
        user = self.get_user(obj)
        if not user:
            return None
        return user.email

    def get_name(self, obj: Withdrawal) -> Optional[str]:
        user = self.get_user(obj)
        if not user:
            return None
        return user.name

    def get_role(self, obj: Withdrawal) -> Optional[str]:
        user = self.get_user(obj)
        if not user:
            return None
        return user.role

    def get_birthday(self, obj: Withdrawal) -> Optional[str]:
        user = self.get_user(obj)
        if not user or user.birthday is None:
            return None
        return user.birthday.isoformat()
