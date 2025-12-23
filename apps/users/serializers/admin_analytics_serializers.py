from typing import Any

from rest_framework import serializers

from apps.users.utils.reason_choices import WithdrawalReason


class BasePeriodCountItemSerializer(serializers.Serializer[Any]):
    """
    기간(월/년) 단위로 집계된 수치를 표현할 때 공통으로 사용하는 Serializer
    """

    period = serializers.CharField()
    count = serializers.IntegerField()


class AdminSignupTrendSerializer(serializers.Serializer[Any]):
    """
    어드민 페이지에서 회원 가입 추세 그래프 데이터를 응답할 때 사용하는 Serializer
    """

    interval = serializers.ChoiceField(choices=["monthly", "yearly"])
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField()
    items = BasePeriodCountItemSerializer(many=True)


class AdminWithdrawalTrendSerializer(serializers.Serializer[Any]):
    """
    어드민 페이지에서 회원 탈퇴 추세 그래프 데이터를 응답할 때 사용하는 Serializer
    """

    interval = serializers.ChoiceField(
        choices=["monthly", "yearly"],
    )
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField()
    items = BasePeriodCountItemSerializer(many=True)


class WithdrawalReasonPercentageItemSerializer(serializers.Serializer[Any]):
    """
    전체 기간 회원 탈퇴 사유 비율 분석에서 개별 탈퇴 사유 한 건을 표현하는 Serializer
    """

    reason = serializers.ChoiceField(
        choices=[choice[0] for choice in WithdrawalReason.choices],
        read_only=True,
    )
    reason_label = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class WithdrawalReasonPercentageSerializer(serializers.Serializer[Any]):
    """
    어드민 페이지 전체 기간 회원 탈퇴 사유 Percentage 분석 API 응답 전체를 나타내는 Serializer
    """

    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField()
    items = WithdrawalReasonPercentageItemSerializer(many=True)


class WithdrawalReasonMonthlyStatsSerializer(serializers.Serializer[Any]):
    """
    어드민 페이지 월별 회원 탈퇴 사유 분석 API 응답 전체를 나타내는 Serializer
    """

    reason = serializers.ChoiceField(
        choices=[choice[0] for choice in WithdrawalReason.choices],
        read_only=True,
    )
    reason_label = serializers.CharField()
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField()
    items = BasePeriodCountItemSerializer(many=True)
