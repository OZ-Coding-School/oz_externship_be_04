from typing import Any, List, cast

from rest_framework import serializers

from apps.study_groups.models import Review


class ReviewCreateSerializer(serializers.Serializer[Review]):
    star_rating = serializers.IntegerField()
    content = serializers.CharField(max_length=300, required=True)

    def validate_star_rating(self, value: int) -> int:
        if not (1 <= value <= 5):
            raise serializers.ValidationError("1부터 5까지의 정수만 입력 가능합니다.")
        return value

    def create(self, validated_data: dict[str, Any]) -> Review:
        user = self.context["request"].user
        study_group = self.context["study_group"]

        review = Review.objects.create(
            user=user,
            study_group=study_group,
            star_rating=validated_data["star_rating"],
            content=validated_data["content"],
        )
        return review


class ReviewSerializer(serializers.Serializer[Review]):
    id = serializers.IntegerField()
    star_rating = serializers.IntegerField()
    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class ReviewUpdateSerializer(serializers.Serializer[Review]):
    id = serializers.IntegerField(read_only=True)
    star_rating = serializers.IntegerField()
    content = serializers.CharField(max_length=300, required=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def validate_star_rating(self, value: int) -> int:
        if not (1 <= value <= 5):
            raise serializers.ValidationError("1부터 5까지의 정수만 입력 가능합니다.")
        return value

    def update(self, instance: Review, validated_data: dict[str, Any]) -> Review:
        instance.star_rating = validated_data["star_rating"]
        instance.content = validated_data["content"]
        instance.save()
        return instance
