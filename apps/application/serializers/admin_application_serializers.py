from __future__ import annotations

from typing import Any

from rest_framework import serializers

from apps.application.models import Application
from apps.lectures.models import CrawledLecture
from apps.recruitment.models import Recruitment, Tag
from apps.users.models import User

from .application_serializers import ApplicationDetailFieldsMixin

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"


class TimestampSerializerMixin(serializers.Serializer[Any]):
    created_at = serializers.DateTimeField(
        format=DATE_TIME_FORMAT,
        read_only=True,
    )
    updated_at = serializers.DateTimeField(
        format=DATE_TIME_FORMAT,
        read_only=True,
    )


class AdminApplicationCommonFieldsMixin(TimestampSerializerMixin, serializers.ModelSerializer[Application]):
    """(Admin) List/Detail 조회에 공통으로 사용되는 필드"""

    id = serializers.IntegerField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Application
        fields = ["id", "uuid", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "uuid", "status", "created_at", "updated_at"]


class AdminApplicantSummarySerializer(serializers.ModelSerializer[User]):
    """(Admin) 지원자 요약 정보"""

    class Meta:
        model = User
        fields = ["id", "nickname", "email"]
        read_only_fields = ["id", "nickname", "email"]


class AdminApplicantDetailSerializer(serializers.ModelSerializer[User]):
    """(Admin) 지원자 상세 정보"""

    class Meta:
        model = User
        fields = ["id", "nickname", "email", "gender", "profile_img_url"]
        read_only_fields = ["id", "nickname", "email", "gender", "profile_img_url"]


class AdminRecruitmentSummarySerializer(serializers.ModelSerializer[Recruitment]):
    """(Admin) 공고 요약 정보"""

    class Meta:
        model = Recruitment
        fields = ["id", "uuid", "title"]
        read_only_fields = ["id", "uuid", "title"]


class AdminRecruitmentLectureSerializer(serializers.ModelSerializer[CrawledLecture]):
    """(Admin) 상세 조회용 강의 정보"""

    class Meta:
        model = CrawledLecture
        fields = ["id", "title", "instructor"]
        read_only_fields = ["id", "title", "instructor"]


class AdminRecruitmentTagSerializer(serializers.ModelSerializer[Tag]):
    """(Admin) 상세 조회용 태그 정보"""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id", "name"]


class AdminRecruitmentDetailSerializer(serializers.ModelSerializer[Recruitment]):
    """(Admin) 지원서 상세 조회에서 보여지는 Recruitment 상세 정보"""

    lectures = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Recruitment
        fields = [
            "id",
            "title",
            "expected_headcount",
            "close_at",
            "lectures",
            "tags",
        ]
        read_only_fields = ["id", "title", "expected_headcount", "close_at", "lectures", "tags"]

    def get_lectures(self, obj: Recruitment) -> Any:
        study_group = obj.study_group
        study_lectures = study_group.studylecture_set.select_related("lecture_id").all()

        lecture_list = [sl.lecture_id for sl in study_lectures]

        from apps.application.serializers.admin_application_serializers import (
            AdminRecruitmentLectureSerializer,
        )

        return AdminRecruitmentLectureSerializer(lecture_list, many=True).data

    def get_tags(self, obj: Recruitment) -> Any:
        recruitment_tags = obj.recruitment_tags.all()
        tags = [rt.tag for rt in recruitment_tags]

        from apps.application.serializers.admin_application_serializers import (
            AdminRecruitmentTagSerializer,
        )

        return AdminRecruitmentTagSerializer(tags, many=True).data


class AdminApplicationListSerializer(AdminApplicationCommonFieldsMixin):
    """(Admin Page) 지원서 목록 조회"""

    recruitment = AdminRecruitmentSummarySerializer(read_only=True)
    applicant = AdminApplicantSummarySerializer(read_only=True)

    class Meta(AdminApplicationCommonFieldsMixin.Meta):
        fields = AdminApplicationCommonFieldsMixin.Meta.fields + ["recruitment", "applicant"]
        read_only_fields = AdminApplicationCommonFieldsMixin.Meta.read_only_fields + ["recruitment", "applicant"]


class AdminApplicationDetailSerializer(AdminApplicationCommonFieldsMixin, ApplicationDetailFieldsMixin):
    """(Admin Page) 지원서 상세 조회"""

    recruitment = AdminRecruitmentDetailSerializer(read_only=True)
    applicant = AdminApplicantDetailSerializer(read_only=True)

    class Meta(AdminApplicationCommonFieldsMixin.Meta):
        fields = (
            AdminApplicationCommonFieldsMixin.Meta.fields
            + ["recruitment", "applicant"]
            + ApplicationDetailFieldsMixin.DETAIL_FIELDS
        )
        read_only_fields = (
            AdminApplicationCommonFieldsMixin.Meta.read_only_fields
            + ["applicant", "recruitment"]
            + ApplicationDetailFieldsMixin.DETAIL_FIELDS
        )
