from apps.schedule.models.group_schedule_model import GroupScheduleModel

class ScheduleCreateService:
    @staticmethod
    def create_schedule(validated_data):

        schedule = GroupScheduleModel.objects.create(
            study_group=validated_data.get("study_group"),
            title=validated_data.get("title"),
            objective=validated_data.get("objective"),
            session_date=validated_data.get("session_date"),
            start_time=validated_data.get("start_time"),
            end_time=validated_data.get("end_time"),
        )
        return schedule