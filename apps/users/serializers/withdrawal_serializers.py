from rest_framework import serializers

from apps.users.models import Withdrawal


class WithdrawalSerializer(serializers.ModelSerializer):
    agree_check = serializers.BooleanField(write_only=True)

    class Meta:
        model = Withdrawal
        fields = ["reason", "reason_detail", "agree_check"]

    def validate_agree_check(self, value):
        if not value:
            raise serializers.ValidationError("회원 탈퇴에 동의해야 탈퇴 가능합니다.")
        return value