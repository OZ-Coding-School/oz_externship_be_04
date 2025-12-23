from datetime import datetime
from typing import Any, Dict, List, Optional

from django.db import transaction

from apps.study_groups.models import (
    GroupMember,
    GroupSchedule,
    ScheduleParticipants,
    StudyGroup,
)


class ScheduleService:
    # 참가자 생성

    @staticmethod
    def _set_participants(schedule: GroupSchedule, participants: List[GroupMember] | None) -> None:
        ScheduleParticipants.objects.filter(schedule=schedule).delete()

        if participants:
            unique_by_id: Dict[int, GroupMember] = {m.id: m for m in participants}
            bulk = [ScheduleParticipants(schedule=schedule, member=member) for member in unique_by_id.values()]
            ScheduleParticipants.objects.bulk_create(bulk)

    # 스케줄 생성

    @staticmethod
    def create_schedule(*, validated_data: Dict[str, Any], group_id: int) -> GroupSchedule:
        study_group = GroupMember.objects.filter(id=group_id).first()
        if study_group is None:
            raise ValueError("스터디 그룹 없음")

        participants = validated_data.pop("participants", [])

        with transaction.atomic():
            schedule = GroupSchedule.objects.create(study_group=study_group, **validated_data)
            ScheduleService._set_participants(schedule, participants)

        return schedule

    # 스케줄 조회

    @staticmethod
    def list_schedules(
        group_id: int, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None
    ) -> List[GroupSchedule]:
        qs = GroupSchedule.objects.filter(study_group_id=group_id)

        if from_date:
            qs = qs.filter(session_date__gte=from_date)
        if to_date:
            qs = qs.filter(session_date__lte=to_date)

        return list(qs.select_related("study_group").prefetch_related("participants__member__user_id"))

    # 스케줄 상세 조회

    @staticmethod
    def retrieve_schedule(*, schedule_id: int) -> Optional[GroupSchedule]:
        return (
            GroupSchedule.objects.select_related("study_group")
            .prefetch_related("participants__member__user_id")
            .filter(id=schedule_id)
            .first()
        )

    # 스케줄 수정

    @staticmethod
    def update_schedule(*, schedule: GroupSchedule, validated_data: Dict[str, Any]) -> GroupSchedule:
        participants: Optional[List[GroupMember]] = validated_data.pop("participants", None)

        for attr, value in validated_data.items():
            setattr(schedule, attr, value)

        with transaction.atomic():
            schedule.save()
            if participants is not None:
                ScheduleService._set_participants(schedule, participants)
        return schedule

    # 스케줄 삭제

    @staticmethod
    def delete_schedule(*, schedule: GroupSchedule) -> None:
        schedule.delete()
