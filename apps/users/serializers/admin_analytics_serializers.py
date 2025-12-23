from typing import Any

from rest_framework import serializers


class BasePeriodCountItemSerializer(serializers.Serializer[Any]):
    period = serializers.CharField()
    count = serializers.IntegerField()


class AdminSignupTrendSerializer(serializers.Serializer[Any]):
    interval = serializers.ChoiceField(choices=["monthly", "yearly"])
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField()
    items = BasePeriodCountItemSerializer(many=True)


class AdminWithdrawalTrendSerializer(serializers.Serializer[Any]):
    interval = serializers.ChoiceField(
        choices=["monthly", "yearly"],
    )
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField()
    items = BasePeriodCountItemSerializer(many=True)


class WithdrawalReasonPercentageItemSerializer(serializers.Serializer[Any]):
    reason = serializers.CharField()
    reason_label = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class WithdrawalReasonPercentageSerializer(serializers.Serializer[Any]):
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField()
    items = WithdrawalReasonPercentageItemSerializer(many=True)


class WithdrawalReasonMonthlyStatsSerializer(serializers.Serializer[Any]):
    reason = serializers.CharField()
    reason_label = serializers.CharField()
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField()
    items = BasePeriodCountItemSerializer(many=True)
