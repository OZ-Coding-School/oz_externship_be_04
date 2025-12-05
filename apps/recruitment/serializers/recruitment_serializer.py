from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from apps.lectures.models import CrawledLecture
from apps.lectures.serializers.crawled_lecture_serializer import (
    CrawledLectureSerializer,
)
from apps.recruitment.models import Recruitment, Tag
from apps.recruitment.serializers.recruitment_attachment_serializer import (
    RecruitmentAttachmentItemSerializer,
    RecruitmentAttachmentUpdateSerializer,
)
from apps.recruitment.serializers.tags import TagSerializer
from apps.study_groups.models import StudyGroup, StudyLecture


class RecruitmentListSerializer(serializers.ModelSerializer[Recruitment]):
    """구인공고 목록 조회"""

    thumbnail_img_url = serializers.SerializerMethodField()
    bookmark_count = serializers.IntegerField(read_only=True, default=0)
    lectures = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Recruitment
        fields = [
            "uuid",
            "title",
            "thumbnail_img_url",
            "expected_headcount",
            "close_at",
            "views_count",
            "bookmark_count",
            "lectures",
            "tags",
        ]
        read_only_fields = fields

    def get_thumbnail_img_url(self, obj: Recruitment) -> Optional[str]:
        first_img = obj.images.first()
        if first_img is not None:
            return getattr(first_img, "img_url", None)
        return getattr(settings, "DEFAULT_THUMBNAIL_URL", None)

    def get_lectures(self, obj: Recruitment) -> List[Dict[str, Any]]:
        """목록용: 최소 정보만 반환"""
        study_group = obj.study_group
        lectures: List[StudyLecture] = list(study_group.studylecture_set.select_related("lecture").all())
        return [
            {
                "id": sl.lecture.id,
                "title": sl.lecture.title,
                "instructor": sl.lecture.instructor or "",
            }
            for sl in lectures
        ]

    def get_tags(self, obj: Recruitment) -> list[dict[str, Any]]:
        return [{"id": rt.tag.id, "name": rt.tag.name} for rt in obj.recruitment_tags.all()]


class RecruitmentDetailSerializer(serializers.ModelSerializer[Recruitment]):
    """구인공고 상세 조회"""

    bookmark_count = serializers.IntegerField(read_only=True, default=0)
    lectures = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()
    image_urls = serializers.SerializerMethodField()

    class Meta:
        model = Recruitment
        fields = [
            "uuid",
            "title",
            "content",
            "estimated_fee",
            "expected_headcount",
            "bookmark_count",
            "views_count",
            "lectures",
            "tags",
            "files",
            "image_urls",
            "close_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "uuid",
            "views_count",
            "bookmark_count",
            "created_at",
            "updated_at",
        ]

    def get_lectures(self, obj: Recruitment) -> List[Dict[str, Any]]:
        study_group = obj.study_group
        lectures: List[StudyLecture] = list(study_group.studylecture_set.select_related("lecture").all())
        crawled_lectures: List[CrawledLecture] = [sl.lecture for sl in lectures]
        return list(CrawledLectureSerializer(crawled_lectures, many=True).data)

    def get_tags(self, obj: Recruitment) -> list[dict[str, Any]]:
        tags = [rt.tag for rt in obj.recruitment_tags.all()]
        return list(TagSerializer(tags, many=True).data)

    def get_files(self, obj: Recruitment) -> list[dict[str, Any]]:
        return [
            {
                "id": a.id,
                "file_name": a.file_name,
                "file_url": a.file_url,
            }
            for a in obj.attachments.all()
        ]

    def get_image_urls(self, obj: Recruitment) -> List[str]:
        """공고 내용에 첨부된 이미지 URL 목록 반환"""
        return [img.img_url for img in obj.images.all()]


class RecruitmentCreateSerializer(serializers.ModelSerializer[Recruitment]):
    """구인공고 생성"""

    study_group = serializers.PrimaryKeyRelatedField(
        queryset=StudyGroup.objects.filter(status="ONGOING"), write_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False)
    files = RecruitmentAttachmentItemSerializer(many=True, required=False)
    image_urls = serializers.ListField(child=serializers.URLField(), max_length=5, required=False, write_only=True)

    class Meta:
        model = Recruitment
        fields = [
            "study_group",
            "title",
            "content",
            "estimated_fee",
            "expected_headcount",
            "close_at",
            "tags",
            "files",
            "image_urls",
        ]
        extra_kwargs = {
            "title": {"required": True, "max_length": 50},
            "content": {"required": True},
            "estimated_fee": {"required": False, "min_value": 0},
            "expected_headcount": {"required": True, "min_value": 1, "max_value": 10},
            "close_at": {"required": True},
        }

    def validate_title(self, value: str) -> str:
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("제목은 최소 5자 이상이어야 합니다.")
        return value

    def validate_content(self, value: str) -> str:
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("내용은 최소 10자 이상이어야 합니다.")
        return value

    def validate_close_at(self, value: Any) -> Any:
        if value < timezone.now():
            raise serializers.ValidationError("마감일시는 현재 시각 이후여야 합니다.")
        return value

    def validate_tags(self, value: list[Tag]) -> list[Tag]:
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError("태그 ID는 중복될 수 없습니다.")
        return value

    def validate_files(self, value: list[dict[str, str]]) -> list[dict[str, str]]:
        filenames = [f.get("file_name") for f in value]
        if len(filenames) != len(set(filenames)):
            raise serializers.ValidationError("중복된 파일명이 있습니다.")
        return value

    def validate_image_urls(self, value: list[str]) -> list[str]:
        return list(set(value))


class RecruitmentUpdateSerializer(serializers.ModelSerializer[Recruitment]):
    """수정(PATCH)"""

    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False)
    files = RecruitmentAttachmentUpdateSerializer(many=True, required=False)
    image_urls = serializers.ListField(child=serializers.URLField(), max_length=5, required=False, write_only=True)

    class Meta:
        model = Recruitment
        fields = ["title", "content", "estimated_fee", "expected_headcount", "tags", "files", "image_urls", "close_at"]

    def validate_title(self, value: str) -> str:
        if value:
            value = value.strip()
            if len(value) < 5:
                raise serializers.ValidationError("제목은 최소 5자 이상이어야 합니다.")
        return value

    def validate_content(self, value: str) -> str:
        if value:
            value = value.strip()
            if len(value) < 10:
                raise serializers.ValidationError("내용은 최소 10자 이상이어야 합니다.")
        return value

    def validate_tags(self, value: list[Tag]) -> list[Tag]:
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError("태그 ID는 중복 될수 없습니다.")
        return value

    def validate_image_urls(self, value: list[str]) -> list[str]:
        return list(set(value))
