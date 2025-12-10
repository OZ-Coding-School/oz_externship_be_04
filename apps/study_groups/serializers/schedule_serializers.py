from datetime import date, datetime, time, timedelta
from typing import Any, TypedDict

from django.utils import timezone
from rest_framework import serializers

from apps.study_groups.models import (
    GroupMember,
    ScheduleParticipants,
    StudyGroup,
)


class GroupScheduleAttrs(TypedDict):
    study_group: StudyGroup
    title: str
    objective: str | None
    session_date: datetime
    start_time: time
    end_time: time
    participants: list[GroupMember]


class GroupScheduleSerializer(serializers.Serializer[Any]):
    participants = serializers.PrimaryKeyRelatedField(
        queryset=GroupMember.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )

    session_date = serializers.DateTimeField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    # 제목&설명 검증
    title = serializers.CharField(
        min_length=1,
        max_length=100,
        allow_blank=False,
        error_messages={
            "blank": "제목을 입력해주세요.",
            "min_length": "제목을 입력해주세요.",
            "max_length": "제목은 100자를 초과할 수 없습니다.",
        },
    )
    objective = serializers.CharField(
        max_length=500,
        allow_blank=True,
        required=False,
        error_messages={
            "max_length": "설명은 500자를 초과할 수 없습니다.",
        },
    )

    # session_date 검증
    def validate_session_date(self, value: datetime) -> datetime:
        if value.date() < timezone.localdate():
            raise serializers.ValidationError({"detail": "session_date는 오늘보다 이전일 수 없습니다."})
        return value

    def validate(self, attrs: GroupScheduleAttrs) -> GroupScheduleAttrs:
        study_group = self.context.get("study_group")
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        participants = attrs.get("participants", [])

        # 시간 검증
        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError({"detail": "시작 시간은 종료 시간과 같거나 이후일 수 없습니다."})
            if (datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)) < timedelta(
                minutes=5
            ):
                raise serializers.ValidationError({"detail": "스케줄의 최소 설정시간은 5분 입니다."})

        # 참가자 검증
        if study_group and participants:
            participant_ids = [m.id for m in participants]

            member_groups = GroupMember.objects.filter(id__in=participant_ids).values_list("id", "study_group_id")

            invalid_ids = [mid for mid, gid in member_groups if gid != study_group.id]

            if invalid_ids:
                ids_str = ", ".join(str(i) for i in invalid_ids)
                raise serializers.ValidationError({"detail": f"유효하지 않은 스터디 그룹 멤버 id: {ids_str}"})

        return attrs

    def to_representation(self, instance: Any) -> dict[str, Any]:
        return {
            "id": instance.id,
            "study_group": instance.study_group.id,
            "title": instance.title,
            "objective": instance.objective,
            "session_date": instance.session_date.isoformat(),
            "start_time": instance.start_time.isoformat(),
            "end_time": instance.end_time.isoformat(),
            "participants": [sp.member.id for sp in ScheduleParticipants.objects.filter(schedule=instance)],
        }
