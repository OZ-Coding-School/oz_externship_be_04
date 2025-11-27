from django.utils import timezone

from rest_framework import serializers

from ...schedule.models.group_schedule_model import GroupScheduleModel
from ...study_groups.models import StudyGroup


class GroupScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupScheduleModel
        fields = "__all__"

    def validate_study_group(self, value):
        if not StudyGroup.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("스터디 그룹이 존재하지 않습니다.")
        return value

    def validate_title(self, value):
        if len(value) < 1:
            raise serializers.ValidationError("제목을 입력해주세요.")
        if len(value) > 100:
            raise serializers.ValidationError("제목은 100자를 초과할 수 없습니다.")
        return value

    def validate_objective(self, value):
        if len(value) > 500:
            raise serializers.ValidationError("설명은 500자를 초과할 수 없습니다.")
        return value

    def validate(self, data):
        if data["session_date"] < timezone.now():
            raise serializers.ValidationError({"detail": "날짜 설정이 잘못 되었습니다."})
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError({"detail": "시간 설정이 잘못 되었습니다."})
        return data
