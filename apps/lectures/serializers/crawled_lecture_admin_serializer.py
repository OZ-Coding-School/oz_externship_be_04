from rest_framework import serializers

from apps.lectures.models import CrawledLecture


class CrawledLectureAdminSerializer(serializers.ModelSerializer[CrawledLecture]):
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
