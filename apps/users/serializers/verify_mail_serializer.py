from django.shortcuts import get_object_or_404

from apps.users import serializers
from apps.users.models.verifiy_mail_model import Verify


class VerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    verify_code = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get("email")
        verify_code = data.get("verify_code")

        access = get_object_or_404(Verify, email=email)
        if verify_code == access.athnt_code:
            return data
