from rest_framework import serializers


class KakaoLoginSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
