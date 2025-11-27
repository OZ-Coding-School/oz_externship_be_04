from django.test import TestCase
from django.utils import timezone
from datetime import timedelta, time, date
from django.contrib.auth import get_user_model

from apps.study_groups.models import StudyGroup, GroupMember
from apps.schedule.models.group_schedule_model import GroupScheduleModel
from apps.schedule.models.schedule_participants_model import ScheduleParticipantsModel
from apps.schedule.serializers.schedule_participants_serializer import ScheduleParticipantsSerializer
from apps.schedule.services.schedule_create import ScheduleCreateService


User = get_user_model()


class ScheduleCreateServiceTest(TestCase):
    def setUp(self):
        # 스터디 그룹 생성
        self.study_group = StudyGroup.objects.create(
            name="테스트 그룹",
            introduction="서비스 테스트용 그룹",
            max_headcount=10,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )

        # 유저 생성 (User 모델 필드에 맞게)
        self.user = User.objects.create(
            email="tester@example.com",
            name="테스트 유저",
            nickname="테멤",
            phone_number="01012345678",
            gender="M",
            birthday=date(2000, 1, 1),
            profile_img_url="http://example.com/profile.png",
            is_active=True,
        )

        # 그룹 멤버 생성
        self.member = GroupMember.objects.create(
            study_group_id=self.study_group,
            user_id=self.user,
            is_leader=False,
        )

        # 스케줄 생성
        self.schedule = GroupScheduleModel.objects.create(
            study_group=self.study_group,
            title="테스트 스케줄",
            objective="서비스 레이어 단위 테스트",
            session_date=timezone.now() + timedelta(days=1),
            start_time=time(19, 0),
            end_time=time(21, 0),
        )

    def test_create_schedule_success(self):
        validated_data = {
            "study_group": self.study_group,
            "title": "테스트 스케줄",
            "objective": "서비스 레이어 단위 테스트",
            "session_date": timezone.now() + timedelta(days=1),
            "start_time": time(19, 0),
            "end_time": time(21, 0),
        }
        schedule = ScheduleCreateService.create_schedule(validated_data)
        self.assertIsInstance(schedule, GroupScheduleModel)
        self.assertEqual(schedule.study_group, self.study_group)

    def test_valid_participant_serializer(self):
        data = {
            "schedule": self.schedule.id,
            "member": self.member.id,
        }
        serializer = ScheduleParticipantsSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        participant = serializer.save()
        self.assertIsInstance(participant, ScheduleParticipantsModel)
        self.assertEqual(participant.schedule, self.schedule)
        self.assertEqual(participant.member, self.member)

    def test_invalid_schedule(self):
        data = {
            "schedule": 9999,  # 존재하지 않는 스케줄
            "member": self.member.id,
        }
        serializer = ScheduleParticipantsSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("schedule", serializer.errors)

    def test_invalid_member(self):
        data = {
            "schedule": self.schedule.id,
            "member": 9999,  # 존재하지 않는 멤버
        }
        serializer = ScheduleParticipantsSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("member", serializer.errors)
