from rest_framework import serializers

from apps.users.utils.reason_choices import WithdrawalReason


class WithdrawalSerializer(serializers.Serializer):  # type: ignore
    reason = serializers.ChoiceField(choices=WithdrawalReason.choices)
    reason_detail = serializers.CharField()
    agree_check = serializers.BooleanField()

    def validate_agree_check(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("회원 탈퇴에 동의해야 탈퇴 가능합니다.")
        return value
