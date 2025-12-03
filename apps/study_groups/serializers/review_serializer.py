from typing import Any

from rest_framework import serializers

from apps.study_groups.models import Review


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "star_rating",
            "content",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields

class ReviewUpsertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["star_rating", "content"]

    def validate_star_rating(self, value: int) -> int:
        if value not in [1,2,3,4,5]:
            raise serializers.ValidationError("별점은 1~5 사이의 정수로 작성해주세요")
        return value

    def create(self, validated_data: dict[str, int]) -> Review:
        request = self.context["request"]
        study_group = self.context["study_group"]

        user = request.user

        return Review.objects.create(
            user=user,
            study_group=study_group,
            **validated_data,
        )



