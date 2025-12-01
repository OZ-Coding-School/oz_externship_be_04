from rest_framework import serializers

from apps.lectures.models import CrawledLecture
from apps.lectures.serializers.category_serializer import CategorySerializer


class AdminCrawledLectureSerializer(serializers.ModelSerializer[CrawledLecture]):
    class Meta:
        model = CrawledLecture
        fields = [
            "id",
            "title",
            "instructor",
            "thumbnail_img_url",
            "platform",
            "url_link",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class AdminCrawledLectureRetrieveSerializer(serializers.ModelSerializer[CrawledLecture]):
    categories = CategorySerializer(source="lecture_categories.category", many=True, read_only=True)
    discounted_price = serializers.IntegerField(source="discount_price", read_only=True)

    class Meta:
        model = CrawledLecture
        fields = [
            "id",
            "title",
            "instructor",
            "description",
            "total_class_time",
            "original_price",
            "discounted_price",
            "difficulty",
            "thumbnail_img_url",
            "average_rating",
            "platform",
            "url_link",
            "categories",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
