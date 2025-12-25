from typing import Any

from rest_framework import serializers

from apps.recruitment.models import RecruitmentAttachment


class RecruitmentAttachmentSerializer(serializers.ModelSerializer[RecruitmentAttachment]):
    """구인공고 첨부파일 조회 (목록/상세/응답 공용)"""

    class Meta:
        model = RecruitmentAttachment
        fields = ["id", "file_name", "file_url", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class RecruitmentAttachmentCreateSerializer(serializers.ModelSerializer[RecruitmentAttachment]):
    """구인공고 첨부파일 생성"""

    class Meta:
        model = RecruitmentAttachment
        fields = ["file_name", "file_url"]
        extra_kwargs = {
            "file_name": {"required": True, "max_length": 50},
            "file_url": {"required": True},
        }


class RecruitmentAttachmentUpdateSerializer(serializers.ModelSerializer[RecruitmentAttachment]):
    """구인공고 첨부파일 수정"""
    id = serializers.IntegerField(required=False)

    class Meta:
        model = RecruitmentAttachment
        fields = ["id", "file_name", "file_url"]
        extra_kwargs = {
            "file_name": {"required": True, "max_length": 255},
            "file_url": {"required": True},
        }


class RecruitmentAttachmentItemSerializer(serializers.Serializer[Any]):
    """첨부파일 단일 아이템 검증용"""

    file_name = serializers.CharField(max_length=50, required=True)
    file_url = serializers.URLField(required=True)
