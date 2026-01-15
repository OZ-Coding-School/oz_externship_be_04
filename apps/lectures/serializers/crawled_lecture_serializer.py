from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.lectures.models import CrawledLecture
from apps.lectures.serializers.category_serializer import CategorySerializer
from apps.lectures.serializers.crawled_lecture_review_serializer import (
    CrawledLectureReviewSerializer,
)


class CrawledLectureSerializer(serializers.ModelSerializer[CrawledLecture]):
    discounted_price = serializers.IntegerField(source="discount_price", read_only=True)

    categories = CategorySerializer(many=True, read_only=True)
    reviews = CrawledLectureReviewSerializer(many=True, read_only=True)

    average_rating = serializers.SerializerMethodField()

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
            "average_rating",
            "platform",
            "url_link",
            "categories",
            "reviews",
        ]
        read_only_fields = fields

    @extend_schema_field(float)
    def get_average_rating(self, obj: CrawledLecture) -> float:
        if obj.average_rating is None:
            return 0.0
        return float(f"{obj.average_rating:.1f}")
