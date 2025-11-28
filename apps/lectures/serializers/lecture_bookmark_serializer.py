from rest_framework import serializers
from apps.lectures.models import LectureBookmark


class LectureBookmarkSerializer(serializers.ModelSerializer[LectureBookmark]):


    class Meta:
        model = LectureBookmark
        fields = ["user", "lecture", "created_at", "updated_at"]
        read_only_fields = ("user", "created_at", "updated_at")


class LectureBookmarkListSerializer(serializers.ModelSerializer[LectureBookmark]):
    id = serializers.IntegerField(source="lecture.id", read_only=True)
    title = serializers.CharField(source="lecture.title", read_only=True)
    instructor = serializers.CharField(source="lecture.instructor", read_only=True)
    total_class_time = serializers.IntegerField(source="lecture.total_class_time", read_only=True)
    original_price = serializers.IntegerField(source="lecture.original_price", read_only=True)
    discounted_price = serializers.IntegerField(source="lecture.discount_price", read_only=True)
    difficulty = serializers.CharField(source="lecture.difficulty", read_only=True)
    thumbnail_img_url = serializers.CharField(source="lecture.thumbnail_img_url", read_only=True)
    platform = serializers.CharField(source="lecture.platform", read_only=True)
    url_link = serializers.CharField(source="lecture.url_link", read_only=True)

    class Meta:
        model = LectureBookmark
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

