from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.study_groups.models import StudyNote, StudyNoteAttachment
from apps.users.models import User


class AuthorSerializer(serializers.ModelSerializer["User"]):
    """작성자 정보"""

    class Meta:
        model = User
        fields = ["id", "nickname", "profile_img_url"]
        read_only_fields = ["id", "nickname", "profile_img_url"]

    def to_representation(self, instance: "User") -> dict[str, Any]:
        data = super().to_representation(instance)
        if not data.get("profile_img_url"):
            data["profile_img_url"] = None
        return data


class FileSerializer(serializers.ModelSerializer["StudyNoteAttachment"]):
    """파일 정보"""

    class Meta:
        model = StudyNoteAttachment
        fields = ["id", "file_name", "file_url"]
        read_only_fields = ["id", "file_name", "file_url"]


class StudyNoteListSerializer(serializers.ModelSerializer["StudyNote"]):
    """노트 목록 조회"""

    author: Any = AuthorSerializer(read_only=True)

    class Meta:
        model = StudyNote
        fields = ["id", "title", "author", "created_at"]


class StudyNoteDetailSerializer(serializers.ModelSerializer["StudyNote"]):
    """노트 상세 조회"""

    author: Any = AuthorSerializer(read_only=True)
    files: Any = FileSerializer(source="attachments", many=True, read_only=True)

    class Meta:
        model = StudyNote
        fields = ["id", "title", "author", "content", "ai_summary", "files", "created_at", "updated_at"]


class BaseStudyNoteSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """스터디 노트 공통 검증 로직"""

    def validate_content(self, value: str) -> str:
        """내용 검증"""
        if value is not None and (not value or not value.strip()):
            raise ValidationError("내용은 공백일 수 없습니다.")
        return value

    def validate_files(self, value: list[dict[str, str]]) -> list[dict[str, str]]:
        """파일 검증"""
        for file in value:
            if "file_name" not in file or "file_url" not in file:
                raise ValidationError("file_name과 file_url은 필수입니다.")
        return value


class StudyNoteCreateSerializer(BaseStudyNoteSerializer):
    """노트 작성 (명세서: images는 list[str], files는 list[{file_name, file_url}])"""

    title: Any = serializers.CharField(max_length=255)
    content: Any = serializers.CharField()
    images: Any = serializers.ListField(child=serializers.URLField(), required=False, default=list)
    files: Any = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()), required=False, default=list
    )


class StudyNoteUpdateSerializer(BaseStudyNoteSerializer):
    """노트 수정"""

    title: Any = serializers.CharField(max_length=255, required=False)
    content: Any = serializers.CharField(required=False)
    images: Any = serializers.ListField(child=serializers.URLField(), required=False)
    files: Any = serializers.ListField(child=serializers.DictField(child=serializers.CharField()), required=False)


class StudyNoteUpdateResponseSerializer(serializers.ModelSerializer["StudyNote"]):
    """노트 수정 응답"""

    files: Any = FileSerializer(source="attachments", many=True, read_only=True)

    class Meta:
        model = StudyNote
        fields = ["id", "title", "content", "files", "updated_at"]
