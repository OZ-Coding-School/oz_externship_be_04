from datetime import date, datetime

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.study_groups.models import (
    GroupMember,
    GroupSchedule,
    ScheduleParticipants,
    StudyGroup,
)


class ScheduleService:
    @staticmethod
    def create_schedule(*, validated_data: dict, group_id: int) -> GroupSchedule:
        participants = validated_data.pop("participants", [])

        try:
            study_group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            raise ValidationError({"detail": "존재하지 않는 스터디 그룹입니다."})

        with transaction.atomic():
            schedule = GroupSchedule.objects.create(
                study_group=study_group,
                **validated_data,
            )

            if participants:
                bulk = [ScheduleParticipants(schedule=schedule, member=member) for member in participants]
                ScheduleParticipants.objects.bulk_create(bulk)

        return schedule
