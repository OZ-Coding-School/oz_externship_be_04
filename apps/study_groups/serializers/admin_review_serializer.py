from rest_framework import serializers

from apps.study_groups.models import Review, StudyGroup
from apps.users.models import User


class AdminStudyGroupSimpleSerializer(serializers.Serializer[StudyGroup]):
    id = serializers.IntegerField()
    name = serializers.CharField()


class AdminReviewAuthorSerializer(serializers.Serializer[User]):
    id = serializers.IntegerField()
    nickname = serializers.CharField()
    email = serializers.EmailField()


class AdminStudyReviewListItemSerializer(serializers.Serializer[Review]):
    id = serializers.IntegerField()
    study_group = AdminStudyGroupSimpleSerializer()
    author = AdminReviewAuthorSerializer(source="user")
    star_rating = serializers.IntegerField()
    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class AdminStudyGroupSerializer(serializers.Serializer[StudyGroup]):
    id = serializers.IntegerField()
    name = serializers.CharField()
    start_at = serializers.DateTimeField(format="%Y-%m-%d")
    end_at = serializers.DateTimeField(format="%Y-%m-%d")
    introduction = serializers.CharField(allow_null=True, required=False)


class AdminStudyReviewDetailSerializer(serializers.Serializer[Review]):
    id = serializers.IntegerField()
    study_group = AdminStudyGroupSerializer()
    author = AdminReviewAuthorSerializer(source="user")
    star_rating = serializers.IntegerField()
    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
