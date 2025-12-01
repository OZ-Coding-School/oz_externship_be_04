from typing import Optional

from django.conf import settings
from rest_framework import serializers

from apps.lectures.models import CrawledLecture
from apps.recruitment.models import Recruitment, RecruitmentBookmarks, Tag


class RecruitmentLectureSerializer(serializers.ModelSerializer[CrawledLecture]):
    class Meta:
        model = CrawledLecture
        fields = ("id", "title", "instructor")


class RecruitmentTagSerializer(serializers.ModelSerializer[Tag]):
    class Meta:
        model = Tag
        fields = ("id", "name")


class RecruitmentCardSerializer(serializers.ModelSerializer[Recruitment]):
    thumbnail_img_url = serializers.SerializerMethodField()
    lectures = RecruitmentLectureSerializer(many=True, read_only=True)
    tags = RecruitmentTagSerializer(many=True, read_only=True)
    bookmark_count = serializers.IntegerField(read_only=True)
    view_count = serializers.IntegerField(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Recruitment
        fields = (
            "id",
            "title",
            "thumbnail_img_url",
            "expected_headcount",
            "lectures",
            "tags",
            "close_at",
            "view_count",
            "bookmark_count",
            "is_bookmarked",
        )

    def get_thumbnail_img_url(self, obj: Recruitment) -> Optional[str]:
        images = getattr(obj, "first_image_list", None)
        first_img = None

        if isinstance(images, list):
            first_img = images[0] if images else None
        elif images is not None and hasattr(images, "first"):
            first_img = images.first()

        img_url = getattr(first_img, "img_url", None)
        if isinstance(img_url, str):
            return img_url

        default_url = getattr(settings, "DEFAULT_THUMBNAIL_IMG_URL", None)
        if isinstance(default_url, str):
            return default_url

        return None

    def get_is_bookmarked(self, obj: Recruitment) -> bool:
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            annotated_val = getattr(obj, "is_bookmarked", None)
            if annotated_val is not None:
                return bool(annotated_val)
            return RecruitmentBookmarks.objects.filter(user_id=request.user, recruitment_id=obj.pk).exists()
        return False
