from typing import Any, Dict

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.users.utils.auth_code import AuthCodeCache


class RestoreWithdrawalSerializer(serializers.Serializer[Any]):

    email = serializers.EmailField(required=True)

    def validate_email(self, value: str) -> str:
        User = get_user_model()

        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error_detail": ["가입된 이메일이 아닙니다."]})

        if user.is_active:
            raise serializers.ValidationError({"error_detail": ["이미 활성화된 유저입니다."]})

        return value


class RestoreEmailCodeSerializer(serializers.Serializer[Any]):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True)

    def validate(self, value: Dict[str, Any]) -> Dict[str, Any]:
        email = value["email"]
        code = value["code"]
        key = f"email:restore:{email}"

        if not AuthCodeCache.verify(key, code):
            raise serializers.ValidationError(
                {"error_detail": {"code": ["이메일 인증 실패 - 이메일 인증코드가 유효하지 않습니다."]}}
            )

        return value

    def save(self, *args: Any, **kwargs: Any) -> Any:
        User = get_user_model()
        email = self.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"error_detail": "해당 유저를 찾을 수 없습니다."})

        with transaction.atomic():
            user.is_active = True
            user.save()

            latest_withdrawal = user.withdrawals.order_by("-created_at").first()
            if latest_withdrawal:
                latest_withdrawal.delete()

        return user
