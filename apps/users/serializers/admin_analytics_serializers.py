from typing import Any

from rest_framework import serializers


class AdminSignupTrendItemSerializer(serializers.Serializer[Any]):
    period = serializers.CharField()
    count = serializers.IntegerField()


class AdminSignupTrendSerializer(serializers.Serializer[Any]):
    interval = serializers.ChoiceField(choices=["monthly", "yearly"])
    from_date = serializers.DateField()
    to_date = serializers.DateField()
    total = serializers.IntegerField()
    items = AdminSignupTrendItemSerializer(many=True)
