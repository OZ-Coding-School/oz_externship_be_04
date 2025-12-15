from typing import Any, Dict, List, Optional, cast

from django.db import transaction
from rest_framework import serializers

from apps.study_groups.models import StudyNote, StudyNoteAttachment, StudyNoteImage


class StudyNoteCreateSerializer(serializers.Serializer[Dict[str, Any]]):
    """노트 작성 요청용 직렬화기"""

    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    images = serializers.ListField(
        child=serializers.URLField(),
        allow_empty=True,
        required=False,
    )
    attachments = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        allow_empty=True,
        required=False,
    )

    def create(self, validated_data: dict[str, Any]) -> StudyNote:  # type: ignore[override]
        # 리스트 데이터는 기본값이 없을 수 있으니 안전하게 꺼낸다.
        images: List[str] = validated_data.pop("images", [])
        raw_attachments: List[dict[str, str]] = validated_data.pop("attachments", [])
        author = validated_data.pop("author")
        study_group = validated_data.pop("study_group")

        with transaction.atomic():
            # 기본 요약은 임시 텍스트로 채운다.
            note = StudyNote.objects.create(
                author=author,
                study_group=study_group,
                ai_summary="TODO: AI 요약",
                **validated_data,
            )
            self._create_images(note, images)
            self._create_attachments(note, raw_attachments)
        return note

    def _create_images(self, note: StudyNote, images: List[str]) -> None:
        if not images:
            return
        image_objs = [StudyNoteImage(study_note=note, img_url=url) for url in images]
        StudyNoteImage.objects.bulk_create(image_objs)

    def _create_attachments(self, note: StudyNote, attachments: List[dict[str, str]]) -> None:
        if not attachments:
            return
        attachment_objs: List[StudyNoteAttachment] = []
        for item in attachments:
            file_url = item.get("file_url")
            file_name = item.get("file_name")
            if not file_url or not file_name:
                continue
            attachment_objs.append(
                StudyNoteAttachment(
                    study_note=note,
                    file_url=file_url,
                    file_name=file_name,
                )
            )
        if attachment_objs:
            StudyNoteAttachment.objects.bulk_create(attachment_objs)


class StudyNoteListSerializer(serializers.ModelSerializer[StudyNote]):
    """노트 목록 응답용 직렬화기"""

    author_nickname = serializers.CharField(source="author.nickname")
    author_profile_img = serializers.CharField(source="author.profile_img_url")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = StudyNote
        fields = [
            "id",
            "title",
            "author_nickname",
            "author_profile_img",
            "created_at",
            "thumbnail",
        ]

    def get_thumbnail(self, obj: StudyNote) -> Optional[str]:
        first_image = obj.images.first()
        return first_image.img_url if first_image else None


class StudyNoteDetailSerializer(serializers.ModelSerializer[StudyNote]):
    """노트 상세 응답용 직렬화기"""

    author_nickname = serializers.CharField(source="author.nickname")
    author_profile_img = serializers.CharField(source="author.profile_img_url")
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M")
    images = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    class Meta:
        model = StudyNote
        fields = [
            "id",
            "title",
            "author_nickname",
            "author_profile_img",
            "content",
            "ai_summary",
            "images",
            "attachments",
            "created_at",
            "updated_at",
        ]

    def get_images(self, obj: StudyNote) -> list[str]:
        return [image.img_url for image in obj.images.all()]

    def get_attachments(self, obj: StudyNote) -> list[dict[str, str]]:
        return [
            {"file_url": attachment.file_url, "file_name": attachment.file_name} for attachment in obj.attachments.all()
        ]
