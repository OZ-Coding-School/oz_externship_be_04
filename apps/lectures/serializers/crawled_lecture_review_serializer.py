from rest_framework import serializers

from apps.lectures.models import CrawledLectureReview


class CrawledLectureReviewSerializer(serializers.ModelSerializer[CrawledLectureReview]):

    class Meta:
        model = CrawledLectureReview
        fields = ["id", "rating", "content", "created_at"]
        read_only_fields = fields
