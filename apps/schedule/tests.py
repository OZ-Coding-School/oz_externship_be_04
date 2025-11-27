from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, time

from apps.study_groups.models import StudyGroup
from apps.schedule.models.group_schedule_model import GroupScheduleModel
from apps.schedule.services.schedule_create import ScheduleCreateService


class ScheduleCreateServiceTest(TestCase):
    def test_create_schedule_success(self):

        study_group = StudyGroup.objects.create(
            name="테스트 그룹",
            introduction="서비스 테스트용 그룹",
            max_headcount=10,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )

        validated_data = {
            "study_group": study_group,
            "title": "테스트 스케줄",
            "objective": "서비스 레이어 단위 테스트",
            "session_date": timezone.now() + timedelta(days=1),
            "start_time": time(19, 0),
            "end_time": time(21, 0),
        }

        schedule = ScheduleCreateService.create_schedule(validated_data)

        self.assertIsInstance(schedule, GroupScheduleModel)
        self.assertEqual(schedule.study_group, study_group)
        self.assertEqual(schedule.title, "테스트 스케줄")
        self.assertEqual(schedule.objective, "서비스 레이어 단위 테스트")
