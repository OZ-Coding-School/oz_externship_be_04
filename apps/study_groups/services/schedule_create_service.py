from apps.study_groups.models import GroupSchedule
from apps.study_groups.serializers.schedule_serializers import GroupScheduleAttrs

class ScheduleCreateService:
    @staticmethod
    def create_schedule(validated_data: GroupScheduleAttrs) -> GroupSchedule:
        return GroupSchedule.objects.create(
            study_group=validated_data["study_group"],
            title=validated_data["title"],
            objective=validated_data.get("objective"),
            session_date=validated_data["session_date"],
            start_time=validated_data["start_time"],
            end_time=validated_data["end_time"],
        )