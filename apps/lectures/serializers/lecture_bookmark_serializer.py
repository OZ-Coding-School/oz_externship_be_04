from typing import Any, Dict

from rest_framework import serializers

from apps.lectures.models import CrawledLecture, LectureBookmark


class BookmarkLectureSerializer(serializers.ModelSerializer[LectureBookmark]):
    discounted_price = serializers.IntegerField(
        source="discount_price",
        read_only=True,
    )

    class Meta:
        model = CrawledLecture
        fields = [
            "id",
            "title",
            "instructor",
            "total_class_time",
            "original_price",
            "discounted_price",
            "difficulty",
            "thumbnail_img_url",
            "platform",
            "url_link",
        ]
        read_only_fields = fields


class LectureBookmarkSerializer(serializers.ModelSerializer[LectureBookmark]):
    class Meta:
        model = LectureBookmark
        fields = ["user", "lecture", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]


class LectureBookmarkListSerializer(BookmarkLectureSerializer):
    def to_representation(self, instance: Any) -> Dict[str, Any]:

        lecture = instance.lecture
        return super().to_representation(lecture)
