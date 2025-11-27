from typing import Any

from rest_framework import serializers

from apps.recruitment.models import RecruitmentImage


class RecruitmentImageSerializer(serializers.ModelSerializer[Any]):
    """
    구인공고 이미지 조회 (목록/상세/응답 공용)
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
        read_only_fields = ["id"]


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

        data = list(set(data))

        return super().to_internal_value(data)
