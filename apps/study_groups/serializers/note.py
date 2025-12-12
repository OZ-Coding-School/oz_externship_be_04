from django.db import transaction
from rest_framework import serializers

from apps.study_groups.models import StudyNote, StudyNoteAttachment, StudyNoteImage


class StudyNoteCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    images = serializers.ListField(child=serializers.URLField(), required=False, allow_empty=True)
    attachments = serializers.ListField(
        child=serializers.DictField(child=serializers.URLField(), allow_empty=False),
        required=False,
        allow_empty=True,
    )

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("제목은 비워둘 수 없습니다.")
        return value.strip()

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("내용은 비워둘 수 없습니다.")
        return value

    def create(self, validated_data):
        images = validated_data.pop("images", [])
        attachments = validated_data.pop("attachments", [])
        study_group = self.context["study_group"]
        author = self.context["author"]

        with transaction.atomic():
            note = StudyNote.objects.create(
                study_group=study_group,
                author=author,
                ai_summary="TODO: AI 요약",
                **validated_data,
            )
            self._create_images(note, images)
            self._create_attachments(note, attachments)
        return note

    def _create_images(self, note, image_urls):
        for url in image_urls:
            StudyNoteImage.objects.create(study_note=note, img_url=url)

    def _create_attachments(self, note, items):
        for item in items:
            file_url = item.get("file_url") or item.get("url")
            if not file_url:
                continue
            file_name = item.get("file_name") or file_url.split("/")[-1]
            StudyNoteAttachment.objects.create(
                study_note=note,
                file_url=file_url,
                file_name=file_name,
            )


class StudyNoteListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    author_nickname = serializers.CharField()
    author_profile_img = serializers.CharField(allow_null=True)
    created_at = serializers.CharField()
    thumbnail = serializers.CharField(allow_null=True)
