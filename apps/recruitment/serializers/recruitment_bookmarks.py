from typing import Optional

from django.conf import settings
from rest_framework import serializers

from apps.lectures.models import CrawledLecture
from apps.recruitment.models import RecruitmentBookmarks, Tag, tags


class RecruitmentLectureSerializer(serializers.ModelSerializer[CrawledLecture]):
    class Meta:
        model = CrawledLecture
        fields = ("id", "title", "instructor")


class RecruitmentTagSerializer(serializers.ModelSerializer[Tag]):
    class Meta:
        model = tags
        fields = ("id", "name")


class RecruitmentBookmarkCardSerializer(serializers.ModelSerializer[RecruitmentBookmarks]):
    #  스터디 구인 공고 제목
    study_group_recruitment_title = serializers.CharField(
        source="recruitment.title",
        read_only=True,
    )

    #  썸네일 이미지
    thumbnail_img_url = serializers.SerializerMethodField()

    #  예상 모집 인원
    expected_member_count = serializers.IntegerField(
        source="recruitment.expected_member_count",
        read_only=True,
    )

    #  강의 목록
    lectures = RecruitmentLectureSerializer(
        source="recruitment.lectures",
        many=True,
        read_only=True,
    )

    # 사용자 정의 태그 목록
    tags = RecruitmentTagSerializer(
        source="recruitment.tags",
        many=True,
        read_only=True,
    )

    #  마감 기한
    close_at = serializers.DateTimeField(
        source="recruitment.deadline",
        read_only=True,
    )

    #  조회수
    view_count = serializers.IntegerField(
        source="recruitment.view_count",
        read_only=True,
    )

    #  북마크 수
    bookmark_count = serializers.IntegerField(
        source="recruitment.bookmark_count",
        read_only=True,
    )

    class Meta:
        model = RecruitmentBookmarks
        fields = (
            "id",
            "study_group_recruitment_title",
            "thumbnail_img_url",
            "expected_member_count",
            "lectures",
            "tags",
            "close_at",
            "view_count",
            "bookmark_count",
        )

    def get_thumbnail_img_url(self, obj: "RecruitmentBookmarks") -> Optional[str]:
        recruitment = getattr(obj, "recruitment_id", None)
        if recruitment is None:
            return getattr(settings, "DEFAULT_THUMBNAIL_IMG_URL", None)

        images = getattr(recruitment, "first_image_list", None)
        first_img: Optional[object] = None

        if isinstance(images, list):
            first_img = images[0] if images else None
        elif images is not None and hasattr(images, "first"):
            first_img = images.first()

        if first_img is not None:
            img_url = getattr(first_img, "img_url", None)
            if img_url is not None:
                return str(img_url)
            url = getattr(first_img, "url", None)
            if url is not None:
                return str(url)

        return getattr(settings, "DEFAULT_THUMBNAIL_IMG_URL", None)
