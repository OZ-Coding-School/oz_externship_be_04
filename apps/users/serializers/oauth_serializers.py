from typing import Any, Dict


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.CharField()
    provider_id = serializers.CharField()

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        return super().validate(attrs)
