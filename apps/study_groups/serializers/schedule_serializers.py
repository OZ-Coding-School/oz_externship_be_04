from datetime import date, datetime, time
from typing import TypedDict

from django.utils import timezone
from rest_framework import serializers

from apps.study_groups.models import GroupMember, StudyGroup
from apps.study_groups.models.schedule import GroupSchedule


class GroupScheduleAttrs(TypedDict):
    study_group: StudyGroup
    title: str
    objective: str | None
    session_date: date
    start_time: time
    end_time: time
    participants: list[int]


class GroupScheduleSerializer(serializers.ModelSerializer[GroupSchedule]):
    participants = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = GroupSchedule
        fields = ["id", "study_group", "title", "objective", "session_date", "start_time", "end_time", "participants"]

    def validate_title(self, value: str) -> str:
        if len(value) < 1:
            raise serializers.ValidationError("제목을 입력해주세요.")
        if len(value) > 100:
            raise serializers.ValidationError("제목은 100자를 초과할 수 없습니다.")
        return value

    def validate_objective(self, value: str | None) -> str | None:
        if len(value) > 500:
            raise serializers.ValidationError("설명은 500자를 초과할 수 없습니다.")
        return value

    def validate_session_date(self, value: date | datetime) -> date:
        today = timezone.localdate()

        if isinstance(value, datetime):
            value_date = value.date()
        else:
            value_date = value

        if value_date < today:
            raise serializers.ValidationError("날짜 설정이 잘못되었습니다.")
        return value

    def validate_start_time(self, value: time) -> time:
        end_time_str = self.initial_data.get("end_time")
        if end_time_str:
            try:
                from datetime import time as dt_time

                h, m, s = map(int, end_time_str.split(":"))
                end_time = dt_time(h, m, s)
                if value >= end_time:
                    raise serializers.ValidationError({"detail": "시간 설정이 잘못 되었습니다."})
            except Exception:
                pass
        return value

    def validate(self, attrs: GroupScheduleAttrs) -> GroupScheduleAttrs:
        study_group = attrs.get("study_group")
        participant_ids: list[int] = attrs.get("participants", [])

        if not participant_ids:
            return attrs

        members = GroupMember.objects.filter(
            study_group_id=study_group,
            user_id__in=participant_ids,
        )
        if members.count() != len(participant_ids):
            raise serializers.ValidationError({"participants": "유효하지 않은 스터디 그룹 멤버가 포함되어 있습니다."})

        return attrs
