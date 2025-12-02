from django.test import TestCase
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import date, timedelta


from apps.study_groups.models import StudyGroup, GroupMember, GroupSchedule
from apps.users.models.users import User


class ScheduleAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

        # 스터디 그룹 생성
        self.group = StudyGroup.objects.create(
            name="테스트그룹",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )

        # 유저 생성
        self.user = User.objects.create(
            email="tester@example.com",
            name="테스터",
            nickname="tester",
            phone_number="01012345678",
            gender="M",
            birthday=date(2000, 1, 1),
            profile_img_url="http://example.com/profile.png",
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

        # 그룹 멤버 생성
        self.member = GroupMember.objects.create(
            study_group_id=self.group,
            user_id=self.user,
            is_leader=False,
        )

    def test_create_schedule(self):
        payload = {
            "title": "첫 스케줄",
            "objective": "설명",
            "session_date": str(timezone.localdate() + timezone.timedelta(days=1)),
            "start_time": "10:00:00",
            "end_time": "12:00:00"
        }

        response = self.client.post(
            f"/study-groups/{self.group.id}/schedules/",
            payload,
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["title"], "첫 스케줄")