from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.recruitment.models import RecruitmentAttachment


class RecruitmentAttachmentSerializer(serializers.ModelSerializer[Any]):
    """구인공고 첨부파일 조회 (목록/상세/응답 공용)"""

    class Meta:
        model = RecruitmentAttachment
        fields = ["id", "file_name", "file_url", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RecruitmentAttachmentCreateSerializer(serializers.ModelSerializer[Any]):
    """구인공고 첨부파일 생성"""

    class Meta:
        model = RecruitmentAttachment
        fields = ["file_name", "file_url"]
        extra_kwargs = {
            "file_name": {"required": True, "max_length": 255},
            "file_url": {"required": True},
        }


class RecruitmentAttachmentUpdateSerializer(serializers.ModelSerializer[Any]):
    """구인공고 첨부파일 수정"""

    class Meta:
        model = RecruitmentAttachment
        fields = ["file_name", "file_url"]


class RecruitmentAttachmentItemSerializer(serializers.Serializer[Any]):
    """첨부파일 단일 아이템 검증용"""

    file_name = serializers.CharField(max_length=255, required=True)
    file_url = serializers.URLField(required=True)


class RecruitmentAttachmentListField(serializers.ListField):
    """첨부파일 리스트 필드 (최대 5개, 중복 방지)"""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("allow_empty", True)
        kwargs.setdefault("max_length", 5)
        kwargs["child"] = RecruitmentAttachmentItemSerializer()
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> list[dict[str, str]]:
        if not isinstance(data, list):
            raise ValidationError("파일은 리스트 형식이어야 합니다.")

        processed = super().to_internal_value(data)

        file_names = {item["file_name"] for item in processed}
        if len(file_names) != len(processed):
            raise ValidationError("중복된 파일명이 있습니다.")

        return processed
