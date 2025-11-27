from typing import Any, Dict

from apps.schedule.models.group_schedule_model import GroupScheduleModel


class ScheduleCreateService:
    @staticmethod
    def create_schedule(validated_data: Dict[str, Any]) -> GroupScheduleModel:
        return GroupScheduleModel.objects.create(
            study_group=validated_data["study_group"],
            title=validated_data["title"],
            objective=validated_data["objective"],
            session_date=validated_data["session_date"],
            start_time=validated_data["start_time"],
            end_time=validated_data["end_time"],
        )
