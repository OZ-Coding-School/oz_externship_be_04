from typing import Any

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.study_groups.models import GroupMember, StudyGroup, StudyLecture


# 스터디 그룹 목록 조회 (Admin)
class AdminStudyGroupListSerializer(serializers.ModelSerializer[StudyGroup]):
    current_headcount = serializers.SerializerMethodField()
    lectures = serializers.SerializerMethodField()
    leader = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroup
        fields = [
            "id",
            "name",
            "introduction",
            "max_headcount",
            "current_headcount",
            "profile_img_url",
            "start_at",
            "end_at",
            "status",
            "created_at",
            "updated_at",
            "lectures",
            "leader",
        ]
        read_only_fields = fields

    @extend_schema_field(serializers.IntegerField())
    def get_current_headcount(self, obj: StudyGroup) -> int:
        return obj.groupmember_study_groups.count()

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_lectures(self, obj: StudyGroup) -> list[dict[str, Any]]:
        return [
            {
                "id": sl.lecture.id,
                "title": sl.lecture.title,
                "instructor": sl.lecture.instructor,
            }
            for sl in obj.studylecture_study_groups.select_related("lecture").all()
        ]

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_leader(self, obj: StudyGroup) -> dict[str, Any] | None:
        leader_member = obj.groupmember_study_groups.filter(is_leader=True).select_related("user_id").first()
        if leader_member:
            return {
                "id": leader_member.user_id.id,
                "nickname": leader_member.user_id.nickname,
                "email": leader_member.user_id.email,
            }
        return None
