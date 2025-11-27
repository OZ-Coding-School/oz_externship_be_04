from datetime import date, time

from django.utils import timezone
from rest_framework import serializers

from apps.schedule.models.group_schedule_model import GroupScheduleModel
from apps.study_groups.models import StudyGroup


class GroupScheduleSerializer(serializers.ModelSerializer[GroupScheduleModel]):

    class Meta:
        model = GroupScheduleModel
        fields = "__all__"

    def validate_study_group(self, value: StudyGroup) -> StudyGroup:
        if not StudyGroup.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("스터디 그룹이 존재하지 않습니다.")
        return value

    def validate_schedule_title(self, value: str) -> str:
        if len(value) < 1:
            raise serializers.ValidationError("제목을 입력해주세요.")
        if len(value) > 100:
            raise serializers.ValidationError("제목은 100자를 초과할 수 없습니다.")
        return value

    def validate_schedule_objective(self, value: str) -> str:
        if len(value) > 500:
            raise serializers.ValidationError("설명은 500자를 초과할 수 없습니다.")
        return value

    def validate_session_date(self, value: date) -> date:
        if value < timezone.localdate():
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
