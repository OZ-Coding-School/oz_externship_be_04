from rest_framework import serializers

from apps.study_groups.models import Review


class StarRatingField(serializers.IntegerField):
    def validate_star_rating(self, value: int):
        valid_values = [choice.value for choice in Review.StarRating]
        if value not in valid_values:
            raise serializers.ValidationError("0부터 5까지의 정수만 입력 가능합니다.")
        return value


class ReviewCreateSerializer(serializers.Serializer):
    star_rating = StarRatingField(required=True)
    content = serializers.CharField(max_length=300, required=True)

    def create(self, validated_data):
        user = self.context["request"].user
        study_group = self.context["study_group"]

        review = Review.objects.create(
            user=user,
            study_group=study_group,
            star_rating=validated_data["star_rating"],
            content=validated_data["content"],
        )
        return review


class ReviewListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    star_rating = serializers.IntegerField()
    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class ReviewUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    star_rating = StarRatingField(required=True)
    content = serializers.CharField(max_length=300, required=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def update(self, instance: Review, validated_data):
        instance.star_rating = validated_data["star_rating"]
        instance.content = validated_data["content"]
        instance.save()
        return instance
