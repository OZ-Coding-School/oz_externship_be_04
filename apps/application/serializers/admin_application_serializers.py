from __future__ import annotations

from rest_framework import serializers

from apps.application.models import Application
from apps.recruitment.models import Recruitment
from apps.users.models import User

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"


class AppliedAtSerializerMixin:
    applied_at = serializers.DateTimeField(source="created_at", format=DATE_TIME_FORMAT, read_only=True)


class AdminApplicantSummarySerializer(serializers.ModelSerializer["User"]):
    """(Admin) 지원자 요약 정보"""

    class Meta:
        model = User
        fields = ["id", "nickname", "email", "profile_img_url"]
        read_only_fields = ["id", "nickname", "email", "profile_img_url"]


class AdminRecruitmentSummarySerializer(serializers.ModelSerializer["Recruitment"]):
    """(Admin) 공고 요약 정보"""

    class Meta:
        model = Recruitment
        fields = ["id", "uuid", "title"]
        read_only_fields = ["id", "uuid", "title"]


class AdminApplicationListSerializer(AppliedAtSerializerMixin, serializers.ModelSerializer["Application"]):
    """(Admin Page) 지원서 목록 조회"""

    id = serializers.IntegerField(read_only=True)
    recruitment = AdminRecruitmentSummarySerializer(read_only=True)
    applicant = AdminApplicantSummarySerializer(read_only=True)
    updated_at = serializers.DateTimeField(format=DATE_TIME_FORMAT, read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "uuid",
            "recruitment",
            "applicant",
            "status",
            "applied_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "recruitment",
            "applicant",
            "status",
            "applied_at",
            "updated_at",
        ]


class AdminApplicationDetailSerializer(AppliedAtSerializerMixin, serializers.ModelSerializer["Application"]):
    """(Admin Page) 지원서 상세 조회"""

    id = serializers.IntegerField(read_only=True)
    recruitment = AdminRecruitmentSummarySerializer(read_only=True)
    applicant = AdminApplicantSummarySerializer(read_only=True)
    updated_at = serializers.DateTimeField(format=DATE_TIME_FORMAT, read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "uuid",
            "applicant",
            "recruitment",
            "self_introduction",
            "motivation",
            "objective",
            "available_time",
            "has_study_experience",
            "study_experience",
            "status",
            "applied_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "applicant",
            "recruitment",
            "self_introduction",
            "motivation",
            "objective",
            "available_time",
            "has_study_experience",
            "study_experience",
            "status",
            "applied_at",
            "updated_at",
        ]
