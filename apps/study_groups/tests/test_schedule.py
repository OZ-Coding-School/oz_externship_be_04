from datetime import timedelta
from typing import cast

from django.test import TestCase
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.study_groups.models import GroupMember, GroupSchedule, StudyGroup
from apps.users.models.users import User


class ScheduleAPITest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create(
            email="tester@example.com",
            name="테스터",
            nickname="tester",
            phone_number="01012345678",
            gender="M",
            birthday="2000-01-01",
            profile_img_url="https://example.com/profile.png",
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

        self.group = StudyGroup.objects.create(
            name="테스트그룹",
            introduction="테스트",
            max_headcount=5,
            profile_img_url="",
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=7),
        )

        self.member = GroupMember.objects.create(
            study_group_id=self.group,
            user_id=self.user,
            is_leader=True,
        )

    def test_create_schedule(self) -> None:
        payload = {
            "title": "첫 스케줄",
            "objective": "설명",
            "session_date": str(timezone.localdate() + timedelta(days=1)),
            "start_time": "10:00:00",
            "end_time": "12:00:00",
            "participants": [self.member.id],
        }

        raw_response = self.client.post(
            f"/api/v1/study-groups/{self.group.id}/schedules/",
            payload,
            format="json",
        )

        response = cast(Response, raw_response)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["title"], "첫 스케줄")

        created = GroupSchedule.objects.get(title="첫 스케줄")
        self.assertEqual(created.study_group, self.group)
