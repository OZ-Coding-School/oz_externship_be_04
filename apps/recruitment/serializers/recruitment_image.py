from typing import Any

from rest_framework import serializers

from apps.recruitment.models import RecruitmentImage


class RecruitmentImageSerializer(serializers.ModelSerializer[Any]):
    """
    구인공고 이미지 조회
    """

    image_url = serializers.URLField(source="img_url", help_text="이미지 URL")

    class Meta:
        model = RecruitmentImage
        fields = [
            "id",
            "image_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]


class RecruitmentImageCreateSerializer(serializers.ModelSerializer[Any]):
    """
    구인공고 이미지 생성
    """

    image_url = serializers.URLField(source="img_url", help_text="이미지 URL")

    class Meta:
        model = RecruitmentImage
        fields = [
            "image_url",
        ]
        extra_kwargs = {"image_url": {"required": True, "help_text": "이미지 URL"}}

    def validate_image_url(self, value: str) -> str:
        """이미지 URL 검증"""
        if not value:
            raise serializers.ValidationError("이미지 URL은 필수입니다.")

        if not value.startswith(("http://", "https://")):
            raise serializers.ValidationError("유효한 URL 형식이 아닙니다.")

        return value


class RecruitmentImageUpdateSerializer(serializers.ModelSerializer[Any]):
    """
    구인공고 이미지 수정
    """

    image_url = serializers.URLField(source="img_url", required=False)

    class Meta:
        model = RecruitmentImage
        fields = [
            "image_url",
        ]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """최소 1개 필드 수정 필요"""
        if not attrs:
            raise serializers.ValidationError("수정할 필드가 최소 1개 이상 필요합니다.")
        return attrs


class RecruitmentImageListField(serializers.ListField):
    """
    이미지 URL 리스트 필드
    """

    child = serializers.URLField()

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("allow_empty", True)
        kwargs.setdefault("max_length", 5)
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> list[str]:
        """리스트 검증"""
        if not isinstance(data, list):
            raise serializers.ValidationError("이미지 URL은 리스트 형식이어야 합니다.")

        if len(data) > 5:
            raise serializers.ValidationError("이미지는 최대 5개까지 등록 가능합니다.")

        data = list(set(data))

        return super().to_internal_value(data)


class RecruitmentImageResponseSerializer(serializers.ModelSerializer[Any]):
    """
    구인공고 이미지 응답
    """

    image_url = serializers.URLField(source="img_url", read_only=True)

    class Meta:
        model = RecruitmentImage
        fields = [
            "id",
            "image_url",
        ]
        read_only_fields = fields
