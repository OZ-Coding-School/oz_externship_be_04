from typing import Any

from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from rest_framework import serializers

from apps.application.models import Application
from apps.lectures.models import CrawledLecture
from apps.recruitment.models import Recruitment, RecruitmentAttachment, Tag
from apps.users.models import User

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"


class TimestampSerializerMixin:  # 시간 포맷
    created_at = serializers.DateTimeField(
        format=DATE_TIME_FORMAT,
        read_only=True,
    )
    updated_at = serializers.DateTimeField(
        format=DATE_TIME_FORMAT,
        read_only=True,
    )


class AdminRecruitmentTagSerializer(serializers.ModelSerializer[Tag]):
    """(Admin) 태그 정보"""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = fields


class AdminRecruitmentLectureDetailSerializer(serializers.ModelSerializer[CrawledLecture]):
    class Meta:
        model = CrawledLecture
        fields = ["id", "title", "instructor", "thumbnail_img_url", "url_link"]
        read_only_fields = ["id", "title", "instructor", "thumbnail_img_url", "url_link"]


class AdminRecruitmentAttachmentSerializer(serializers.ModelSerializer[RecruitmentAttachment]):
    class Meta:
        model = RecruitmentAttachment
        fields = ["id", "file_name", "file_url"]
        read_only_fields = fields


class AdminApplicantSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["id", "nickname", "email"]
        read_only_fields = fields


class AdminRecruitmentApplicationSummarySerializer(serializers.ModelSerializer[Application]):
    applicant = AdminApplicantSerializer(read_only=True)
    created_at = serializers.DateTimeField(format=DATE_TIME_FORMAT)

    class Meta:
        model = Application
        fields = ["id", "applicant", "status", "created_at"]
        read_only_fields = fields


class AdminRecruitmentListSerializer(TimestampSerializerMixin, serializers.ModelSerializer[Recruitment]):
    """(관리자용) 구인공고 목록 조회"""

    tags = serializers.SerializerMethodField()
    bookmark_count = serializers.IntegerField()

    class Meta:
        model = Recruitment
        fields = [
            "id",
            "title",
            "tags",
            "close_at",
            "is_closed",
            "views_count",
            "bookmark_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    @extend_schema_field(AdminRecruitmentTagSerializer(many=True))
    def get_tags(self, obj: Recruitment) -> Any:
        tag_list = [rt.tag for rt in obj.recruitment_tags.all()]
        return AdminRecruitmentTagSerializer(tag_list, many=True).data


@extend_schema_serializer(component_name="AdminRecruitmentDetailResponse")
class AdminRecruitmentDetailSerializer(TimestampSerializerMixin, serializers.ModelSerializer[Recruitment]):
    """(관리자용) 구인공고 상세 조회"""

    tags = serializers.SerializerMethodField()
    lectures = serializers.SerializerMethodField()
    files = serializers.SerializerMethodField()
    applications = serializers.SerializerMethodField()
    bookmark_count = serializers.SerializerMethodField()

    class Meta:
        model = Recruitment
        fields = [
            "id",
            "uuid",
            "title",
            "content",
            "expected_headcount",
            "estimated_fee",
            "close_at",
            "is_closed",
            "views_count",
            "bookmark_count",
            "created_at",
            "updated_at",
            "tags",
            "lectures",
            "files",
            "applications",
        ]
        read_only_fields = fields

    @extend_schema_field(AdminRecruitmentTagSerializer(many=True))
    def get_tags(self, obj: Recruitment) -> Any:
        tag_list = [rt.tag for rt in obj.recruitment_tags.all()]
        return AdminRecruitmentTagSerializer(tag_list, many=True).data

    @extend_schema_field(AdminRecruitmentAttachmentSerializer(many=True))
    def get_files(self, obj: Recruitment) -> Any:
        return AdminRecruitmentAttachmentSerializer(obj.attachments.all(), many=True).data

    @extend_schema_field(AdminRecruitmentLectureDetailSerializer(many=True))
    def get_lectures(self, obj: Recruitment) -> Any:
        study_group = obj.study_group
        study_lectures = study_group.studylecture_study_groups.all()
        lecture_list = [sl.lecture for sl in study_lectures if sl.lecture is not None]
        return AdminRecruitmentLectureDetailSerializer(lecture_list, many=True).data

    @extend_schema_field(AdminRecruitmentApplicationSummarySerializer(many=True))
    def get_applications(self, obj: Recruitment) -> Any:
        apps = obj.applications.all()
        return AdminRecruitmentApplicationSummarySerializer(apps, many=True, context=self.context).data

    @extend_schema_field(serializers.IntegerField())
    def get_bookmark_count(self, obj: Recruitment) -> int:
        return getattr(obj, "bookmark_count", obj.recruitment_bookmarks.count())
