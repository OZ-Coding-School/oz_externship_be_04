from datetime import datetime, time
from typing import TypedDict

from django.utils import timezone
from rest_framework import serializers

from apps.study_groups.models import GroupMember, StudyGroup
from apps.study_groups.models.schedule import GroupSchedule, ScheduleParticipants


class GroupScheduleAttrs(TypedDict):
    study_group: StudyGroup
    title: str
    objective: str | None
    session_date: datetime
    start_time: time
    end_time: time


class GroupScheduleSerializer(serializers.ModelSerializer[GroupSchedule]):

    class Meta:
        model = GroupSchedule
        fields = "__all__"

    def validate_title(self, value: str) -> str:
        if len(value) < 1:
            raise serializers.ValidationError("제목을 입력해주세요.")
        if len(value) > 100:
            raise serializers.ValidationError("제목은 100자를 초과할 수 없습니다.")
        return value

    def validate_objective(self, value: str) -> str:
        if len(value) > 500:
            raise serializers.ValidationError("설명은 500자를 초과할 수 없습니다.")
        return value

    def validate_session_date(self, value: datetime) -> datetime:
        if value.date() < timezone.localdate():
            raise serializers.ValidationError({"detail": "날짜 설정이 잘못 되었습니다."})
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
        return attrs


class ScheduleParticipantsAttrs(TypedDict):
    group_schedule: GroupSchedule
    group_member: GroupMember


class ScheduleParticipantsSerializer(serializers.ModelSerializer[ScheduleParticipants]):
    class Meta:
        model = ScheduleParticipants
        fields = "__all__"

    def validate(self, attrs: ScheduleParticipantsAttrs) -> ScheduleParticipantsAttrs:
        schedule = attrs.get("group_schedule")
        member = attrs.get("group_member")

        if ScheduleParticipants.objects.filter(group_schedule=schedule, group_member=member).exists():
            raise serializers.ValidationError("이미 참가자로 등록되어 있습니다.")

        if schedule.study_group_id != member.study_group_id:
            raise serializers.ValidationError("스케줄과 멤버의 스터디 그룹이 일치하지 않습니다.")

        return attrs
