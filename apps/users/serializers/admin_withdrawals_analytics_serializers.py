from typing import Any

from rest_framework import serializers


class AdminWithdrawalTrendItemSerializer(serializers.Serializer[Any]):
    period = serializers.CharField()
    count = serializers.IntegerField()


class AdminWithdrawalTrendSerializer(serializers.Serializer[Any]):
    interval = serializers.ChoiceField(
        choices=["monthly", "yearly"],
    )
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField()
    items = AdminWithdrawalTrendItemSerializer(many=True)


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
