from rest_framework import serializers
from apps.users.models import User


class SocialLoginRequestSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "profile_img_url",
        ]
