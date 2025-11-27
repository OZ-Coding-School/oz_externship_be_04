from rest_framework import serializers

from ...study_groups.models import GroupMember
from ..models.group_schedule_model import GroupScheduleModel
from ..models.schedule_participants_model import ScheduleParticipantsModel


class ScheduleParticipantsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ScheduleParticipantsModel
        fields = "__all__"

    def validate_group_schedule(self, value):
        if not GroupScheduleModel.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("해당 스케줄이 존재하지 않습니다.")
        return value

    def validate_group_member(self, value):
        if not GroupMember.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("해당 맴버가 존재하지 않습니다.")
        return value
