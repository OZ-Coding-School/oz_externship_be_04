from typing import Any

from apps.study_groups.models import GroupMember, GroupSchedule, ScheduleParticipants


class ScheduleService:
    @staticmethod
    def create_schedule(validated_data: dict[str, Any]) -> GroupSchedule:
        print("create_schedule received:", validated_data)

        participant_ids = validated_data.pop("participants", [])
        schedule = GroupSchedule.objects.create(**validated_data)

        if participant_ids:
            members = GroupMember.objects.filter(
                study_group_id=schedule.study_group,
                user_id__in=participant_ids,
            )
            bulk = [ScheduleParticipants(schedule=schedule, member=m) for m in members]
            ScheduleParticipants.objects.bulk_create(bulk)

        return schedule
