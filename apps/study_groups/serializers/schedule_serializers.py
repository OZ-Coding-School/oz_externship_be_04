from datetime import date, datetime, time, timedelta
from typing import TypedDict

from django.utils import timezone
from rest_framework import serializers

from apps.study_groups.models import GroupMember, StudyGroup


class GroupScheduleAttrs(TypedDict):
    study_group: StudyGroup
    title: str
    objective: str | None
    session_date: datetime
    start_time: time
    end_time: time
    participants: list[GroupMember]


class GroupScheduleSerializer(serializers.Serializer):
    participants = serializers.PrimaryKeyRelatedField(
        queryset=GroupMember.objects.all(),
        many=True,
        write_only=True,
    )
    session_date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

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

    def validate_session_date(self, value: date) -> date:
        if value < timezone.localdate():
            raise serializers.ValidationError("session_date는 오늘보다 이전일 수 없습니다.")
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
            invalid_ids = []
            for member in participants:
                if member.study_group_id.id != study_group.id:
                    invalid_ids.append(member.id)

            if invalid_ids:
                ids_str = ", ".join(str(i) for i in invalid_ids)
                raise serializers.ValidationError({"participants": f"유효하지 않은 스터디 그룹 멤버 id: {ids_str}"})

        return attrs
