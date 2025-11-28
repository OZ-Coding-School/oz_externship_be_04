from rest_framework import serializers

from apps.lectures.models import CrawledLecture
from apps.lectures.serializers.category_serializer import CategorySerializer
from apps.lectures.serializers.crawled_lecture_review_serializer import (
    CrawledLectureReviewSerializer,
)


class CrawledLectureSerializer(serializers.ModelSerializer[CrawledLecture]):
    # categories = CategorySerializer(source="lecture_categories.category", many=True, read_only=True) 실기능
    # reviews = CrawledLectureReviewSerializer(many=True, read_only=True) 실기능
    categories = CategorySerializer(source="mock_crawled_lecture_categories", many=True, read_only=True)  # mock
    discounted_price = serializers.IntegerField(source="discount_price", read_only=True)
    reviews = CrawledLectureReviewSerializer(source="mock_crawled_lecture_reviews", many=True, read_only=True)  # mock

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
