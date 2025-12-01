from rest_framework import serializers

from apps.lectures.models import CrawledLecture


class BookmarkLectureSerializer(serializers.ModelSerializer[CrawledLecture]):

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
