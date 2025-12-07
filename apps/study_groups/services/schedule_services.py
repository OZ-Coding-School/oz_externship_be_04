from typing import Any, Dict, List, Optional

from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.study_groups.models import (
    GroupMember,
    GroupSchedule,
    ScheduleParticipants,
    StudyGroup,
)


class ScheduleService:
    # 스케줄 생성

    @staticmethod
    def create_schedule(*, validated_data: Dict[str, Any], group_id: int) -> GroupSchedule:
        """
        validated_data['participants']는 GroupMember 객체 리스트(또는 빈 리스트)라고 가정.
        리더 자동 추가 로직 제거: 전달된 participants만 참가자로 등록.
        """
        participants: List[GroupMember] = validated_data.pop("participants", [])

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
                unique_by_id: Dict[int, GroupMember] = {m.id: m for m in participants}
                bulk = [ScheduleParticipants(schedule=schedule, member=member) for member in unique_by_id.values()]
                ScheduleParticipants.objects.bulk_create(bulk)

        return schedule

    # 스케줄 조회
    @staticmethod
    def list_schedules(*, group_id: int) -> List[GroupSchedule]:
        return list(GroupSchedule.objects.filter(study_group_id=group_id))

    # 스케줄 상세 조회
    @staticmethod
    def retrieve_schedule(*, schedule_id: int) -> GroupSchedule:
        try:
            return GroupSchedule.objects.get(id=schedule_id)
        except GroupSchedule.DoesNotExist:
            raise ValidationError({"detail": "존재하지 않는 스케줄입니다."})

    # 스케줄 수정
    @staticmethod
    def update_schedule(*, schedule: GroupSchedule, validated_data: Dict[str, Any]) -> GroupSchedule:
        participants: Optional[List[GroupMember]] = validated_data.pop("participants", None)

        for attr, value in validated_data.items():
            setattr(schedule, attr, value)

        with transaction.atomic():
            schedule.save()

            if participants is not None:
                ScheduleParticipants.objects.filter(schedule=schedule).delete()

                if participants:
                    unique_by_id: Dict[int, GroupMember] = {m.id: m for m in participants}
                    bulk = [ScheduleParticipants(schedule=schedule, member=member) for member in unique_by_id.values()]
                    ScheduleParticipants.objects.bulk_create(bulk)

    # 스케줄 삭제
    @staticmethod
    def delete_schedule(*, schedule: GroupSchedule) -> None:
        schedule.delete()
