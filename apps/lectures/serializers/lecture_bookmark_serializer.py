from rest_framework import serializers
from apps.lectures.models import LectureBookmark
from apps.lectures.serializers.bookmark_lecture_serializer import BookmarkLectureSerializer



class LectureBookmarkSerializer(serializers.ModelSerializer[LectureBookmark]):

    class Meta:
        model = LectureBookmark
        fields = ["user", "lecture", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]


class LectureBookmarkListSerializer(serializers.ModelSerializer[LectureBookmark]):
    class Meta:
        model = LectureBookmark
        fields = ["lecture"]

    def to_representation(self, instance):
        lecture_data = BookmarkLectureSerializer(instance.lecture).data
        return lecture_data

