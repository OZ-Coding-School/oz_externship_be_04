from rest_framework import serializers

from apps.schedule.models.group_schedule_model import GroupScheduleModel
from apps.schedule.models.schedule_participants_model import ScheduleParticipantsModel
from apps.study_groups.models import GroupMember


class ScheduleParticipantsSerializer(serializers.ModelSerializer[ScheduleParticipantsModel]):

    class Meta:
        model = ScheduleParticipantsModel
        fields = "__all__"

    def validate_group_schedule(self, value: GroupScheduleModel) -> GroupScheduleModel:
        if not GroupScheduleModel.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("해당 스케줄이 존재하지 않습니다.")
        return value

    def validate_group_member(self, value: GroupMember) -> GroupMember:
        if not GroupMember.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("해당 맴버가 존재하지 않습니다.")
        return value
