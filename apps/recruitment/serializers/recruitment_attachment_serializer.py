from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.recruitment.models import RecruitmentAttachment


class RecruitmentAttachmentSerializer(serializers.ModelSerializer[Any]):
    """
    구인공고 첨부파일 조회 (목록/상세/응답 공용)
    """

    class Meta:
        model = RecruitmentAttachment
        fields = [
            "id",
            "file_name",
            "file_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id"]


class RecruitmentAttachmentCreateSerializer(serializers.ModelSerializer[Any]):
    """
    구인공고 첨부파일 생성
    """

    class Meta:
        model = RecruitmentAttachment
        fields = [
            "file_name",
            "file_url",
        ]
        extra_kwargs = {
            "file_name": {
                "required": True,
                "max_length": 255,
                "help_text": "파일명 (확장자 포함)",
            },
            "file_url": {
                "required": True,
                "help_text": "파일 URL",
            },
        }


class RecruitmentAttachmentUpdateSerializer(serializers.ModelSerializer[Any]):
    """
    구인공고 첨부파일 수정
    """

    class Meta:
        model = RecruitmentAttachment
        fields = [
            "file_name",
            "file_url",
        ]
        extra_kwargs = {
            "file_name": {"required": False},
            "file_url": {"required": False},
        }


class RecruitmentAttachmentListField(serializers.ListField):
    """
    첨부파일 리스트 필드
    """

    child = serializers.DictField(child=serializers.CharField())

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("required", False)
        kwargs.setdefault("allow_empty", True)
        kwargs.setdefault("max_length", 5)
        super().__init__(**kwargs)

    def to_internal_value(self, data: Any) -> list[dict[str, str]]:
        """리스트 포맷 및 중복 검증"""

        if not isinstance(data, list):
            raise ValidationError("파일은 리스트 형식이어야 합니다.")

        processed = super().to_internal_value(data)

        file_names = set()
        for item in processed:
            if "file_name" not in item or "file_url" not in item:
                raise ValidationError("첨부파일은 file_name과 file_url을 포함해야 합니다.")

            if item["file_name"] in file_names:
                raise ValidationError("중복된 파일명이 있습니다.")

            file_names.add(item["file_name"])

        return processed
