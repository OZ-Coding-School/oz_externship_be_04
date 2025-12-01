from __future__ import annotations

from rest_framework import serializers

from apps.application.models import Application
from apps.recruitment.models import Recruitment
from apps.users.models import User

from .application_serializers import ApplicationDetailFieldsMixin

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"


class AppliedAtSerializerMixin(serializers.Serializer):
    applied_at = serializers.SerializerMethodField()

    def get_applied_at(self, obj):
        created = getattr(obj, "created_at", None)
        if created is None:
            return None
        return created.strftime("%Y-%m-%d %H:%M")


class AdminApplicationCommonFieldsMixin(AppliedAtSerializerMixin, serializers.ModelSerializer["Application"]):
    """Admin List/Detail 조회에 공통으로 사용되는 필드"""

    id = serializers.IntegerField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    updated_at = serializers.DateTimeField(format=DATE_TIME_FORMAT, read_only=True)

    class Meta:
        model = Application
        fields = ["id", "uuid", "status", "applied_at", "updated_at"]
        read_only_fields = ["id", "uuid", "status", "applied_at", "updated_at"]


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


class AdminApplicationListSerializer(AdminApplicationCommonFieldsMixin):
    """(Admin Page) 지원서 목록 조회"""

    recruitment = AdminRecruitmentSummarySerializer(read_only=True)
    applicant = AdminApplicantSummarySerializer(read_only=True)

    class Meta(AdminApplicationCommonFieldsMixin.Meta):
        fields = AdminApplicationCommonFieldsMixin.Meta.fields + ["recruitment", "applicant"]
        read_only_fields = AdminApplicationCommonFieldsMixin.Meta.read_only_fields + ["recruitment", "applicant"]


class AdminApplicationDetailSerializer(AdminApplicationCommonFieldsMixin, ApplicationDetailFieldsMixin):
    """(Admin Page) 지원서 상세 조회"""

    recruitment = AdminRecruitmentSummarySerializer(read_only=True)
    applicant = AdminApplicantSummarySerializer(read_only=True)

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
