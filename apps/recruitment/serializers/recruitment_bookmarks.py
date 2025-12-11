from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from django.conf import settings
from rest_framework import serializers

from apps.recruitment.models import Recruitment, RecruitmentBookmarks


class RecruitmentInBookmarkSerializer(serializers.Serializer[Any]):
    """북마크 목록에서 사용되는 공고 정보 (명세서 형식)"""

    uuid = serializers.UUIDField(read_only=True)
    title = serializers.CharField(read_only=True)
    thumbnail_img_url = serializers.SerializerMethodField()
    expected_headcount = serializers.IntegerField(read_only=True)
    close_at = serializers.DateTimeField(read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    bookmark_count = serializers.IntegerField(read_only=True)
    lectures = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    def get_thumbnail_img_url(self, obj: Recruitment) -> Optional[str]:
        """첫 번째 이미지를 썸네일로 반환"""
        first_img = obj.images.first()
        if first_img is not None:
            return getattr(first_img, "img_url", None)
        return getattr(settings, "DEFAULT_THUMBNAIL_URL", None)

    def get_lectures(self, obj: Recruitment) -> List[Dict[str, Any]]:
        """강의 목록 반환"""
        study_group = obj.study_group
        lectures = list(study_group.studylecture_set.all())
        return [
            {
                "id": sl.lecture.id,
                "title": sl.lecture.title,
                "instructor": sl.lecture.instructor or "",
            }
            for sl in lectures
        ]

    def get_tags(self, obj: Recruitment) -> List[Dict[str, Any]]:
        """태그 목록 반환"""
        return [{"id": rt.tag.id, "name": rt.tag.name} for rt in obj.recruitment_tags.all()]


class RecruitmentBookmarkCardSerializer(serializers.ModelSerializer[RecruitmentBookmarks]):
    """북마크 목록 조회 (명세서 형식 - recruitment 객체 포함)"""

    recruitment = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentBookmarks
        fields = ("id", "recruitment")
        read_only_fields = fields

    def get_recruitment(self, obj: RecruitmentBookmarks) -> Dict[str, Any]:
        """명세서에 맞는 recruitment 객체 반환"""
        recruitment = obj.recruitment_id
        return RecruitmentInBookmarkSerializer(recruitment).data


class RecruitmentBookmarkCreateSerializer(serializers.Serializer[RecruitmentBookmarks]):
    recruitment_uuid = serializers.UUIDField()

    def validate_recruitment_uuid(self, value: UUID) -> UUID:
        return value
