from __future__ import annotations

from typing import Any, Dict

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.application.models import Application
from apps.recruitment.models import Recruitment
from apps.users.models import User

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"


class AppliedAtSerializerMixin:
    applied_at = serializers.DateTimeField(source="created_at", format=DATE_TIME_FORMAT, read_only=True)


class ApplicationCommonFieldsMixin(AppliedAtSerializerMixin, serializers.ModelSerializer["Application"]):
    """모든 List/Detail 조회에 공통으로 포함되는 필드 정의"""

    uuid = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    updated_at = serializers.DateTimeField(format=DATE_TIME_FORMAT, read_only=True)

    class Meta:
        model = Application
        fields = ["uuid", "status", "applied_at", "updated_at"]
        read_only_fields = ["uuid", "status", "applied_at", "updated_at"]


class ApplicationDetailFieldsMixin:
    """모든 상세 조회에 공통으로 포함되는 지원서 상세 내용 필드"""

    self_introduction = serializers.CharField(read_only=True)
    motivation = serializers.CharField(read_only=True)
    objective = serializers.CharField(read_only=True)
    available_time = serializers.CharField(read_only=True)
    has_study_experience = serializers.BooleanField(read_only=True)
    study_experience = serializers.CharField(read_only=True)

    DETAIL_FIELDS = [
        "self_introduction",
        "motivation",
        "objective",
        "available_time",
        "has_study_experience",
        "study_experience",
    ]


class ApplicantSummarySerializer(serializers.ModelSerializer["User"]):
    """지원자 요약 정보"""

    class Meta:
        model = User  # 002, 003에서 요구하는 필드: 닉네임, 성별, 프로필 이미지 url
        fields = ["nickname", "gender", "profile_img_url"]
        read_only_fields = ["nickname", "gender", "profile_img_url"]


class RecruitmentSummarySerializer(serializers.ModelSerializer["Recruitment"]):
    """공고 요약 정보"""

    class Meta:
        model = Recruitment  # 006에서 요구하는 필드: 제목, 예상 모집 인원, 마감 기한
        fields = ["uuid", "title", "expected_headcount", "close_at"]
        read_only_fields = ["uuid", "title", "expected_headcount", "close_at"]


class ApplicationCreateSerializer(serializers.ModelSerializer["Application"]):
    """REQ-APLY-001: 지원서 작성"""

    class Meta:
        model = Application
        fields = [
            "recruitment",
            "self_introduction",
            "motivation",
            "objective",
            "available_time",
            "has_study_experience",
            "study_experience",
        ]

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        has_exp = data.get("has_study_experience")
        study_exp_content: str = str(data.get("study_experience") or "").strip()

        if has_exp:
            if not study_exp_content:
                raise ValidationError(
                    {"study_experience": "스터디 경험 유무를 '있음'으로 선택한 경우 상세 내용을 기재해야 합니다."}
                )
        else:
            data["study_experience"] = ""

        return data


class RecruiterApplicationListSerializer(ApplicationCommonFieldsMixin):
    """REQ-APLY-002: 작성자용 목록 조회"""

    applicant = ApplicantSummarySerializer(read_only=True)
    available_time = serializers.CharField(read_only=True)
    has_study_experience = serializers.BooleanField(read_only=True)

    class Meta(ApplicationCommonFieldsMixin.Meta):
        fields = ApplicationCommonFieldsMixin.Meta.fields + ["applicant", "available_time", "has_study_experience"]
        read_only_fields = ApplicationCommonFieldsMixin.Meta.read_only_fields + [
            "applicant",
            "available_time",
            "has_study_experience",
        ]


class RecruiterApplicationDetailSerializer(ApplicationCommonFieldsMixin, ApplicationDetailFieldsMixin):
    """REQ-APLY-003: 작성자용 상세 조회"""

    applicant = ApplicantSummarySerializer(read_only=True)

    class Meta(ApplicationCommonFieldsMixin.Meta):
        fields = (
            ApplicationCommonFieldsMixin.Meta.fields
            + [
                "applicant",
            ]
            + ApplicationDetailFieldsMixin.DETAIL_FIELDS
        )

        read_only_fields = (
            ApplicationCommonFieldsMixin.Meta.read_only_fields
            + [
                "applicant",
            ]
            + ApplicationDetailFieldsMixin.DETAIL_FIELDS
        )


class ApplicantApplicationListSerializer(ApplicationCommonFieldsMixin):
    """REQ-APLY-006: 내가 지원한 목록"""

    recruitment = RecruitmentSummarySerializer(read_only=True)

    class Meta(ApplicationCommonFieldsMixin.Meta):
        fields = ApplicationCommonFieldsMixin.Meta.fields + ["recruitment"]
        read_only_fields = ApplicationCommonFieldsMixin.Meta.read_only_fields + ["recruitment"]


class ApplicantApplicationDetailSerializer(ApplicationCommonFieldsMixin, ApplicationDetailFieldsMixin):
    """REQ-APLY-007: 본인 지원 내역 상세"""

    class Meta(ApplicationCommonFieldsMixin.Meta):
        fields = ApplicationCommonFieldsMixin.Meta.fields + ApplicationDetailFieldsMixin.DETAIL_FIELDS
        read_only_fields = (
            ApplicationCommonFieldsMixin.Meta.read_only_fields + ApplicationDetailFieldsMixin.DETAIL_FIELDS
        )
