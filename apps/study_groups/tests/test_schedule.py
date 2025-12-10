from datetime import date, time, timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.study_groups.models import (
    GroupMember,
    GroupSchedule,
    ScheduleParticipants,
    StudyGroup,
)
from apps.users.models.users import User


class ScheduleAPITest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient(raise_request_exception=True)
        self.user = User.objects.create(
            email="test@test.com",
            name="테스트",
            nickname="테스트",
            phone_number="01012341234",
            gender="M",
            birthday="1995-01-01",
            profile_img_url="http://test.com/profile.jpg",
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

        self.member1 = GroupMember.objects.create(
            study_group_id=self.group,
            user_id=self.user,
            is_leader=True,
        )

        self.member2_user = User.objects.create(
            email="test2@test.com",
            name="테스트2",
            nickname="테스트2",
            phone_number="01099998888",
            gender="F",
            birthday="1996-01-01",
            profile_img_url="http://test.com/profile2.jpg",
            is_active=True,
        )

        self.member2 = GroupMember.objects.create(
            user_id=self.member2_user,
            study_group_id=self.group,
        )
        self.schedule_create_url = f"/api/v1/study-groups/{self.group.id}/schedules"

        self.base_payload = {
            "title": "파이썬 자료형 학습",
            "objective": "파이썬 자료형 마스터하기",
            "session_date": "2026-11-20",
            "start_time": "10:00:00",
            "end_time": "11:00:00",
            "participants": [self.member1.id],
        }

        # 스케줄 생성 테스트

    def test_create_schedule(self) -> None:
        response = self.client.post(
            self.schedule_create_url,
            self.base_payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GroupSchedule.objects.count(), 1)
        self.assertEqual(ScheduleParticipants.objects.count(), 1)

        # 스케줄 목록 조회

    def test_list_schedule(self) -> None:
        schedule = GroupSchedule.objects.create(
            study_group=self.group,
            title="조회 테스트",
            objective="",
            session_date=timezone.now() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )

        url = f"/api/v1/study-groups/{self.group.id}/schedules"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]), 1)

        # 스케줄 상세 조회

    def test_detail_schedule(self) -> None:
        schedule = GroupSchedule.objects.create(
            study_group=self.group,
            title="상세 테스트",
            objective="",
            session_date=timezone.now() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )

        url = f"/api/v1/study-groups/{self.group.id}/schedules/{schedule.id}"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["title"], "상세 테스트")

        # 스케줄 수정

    def test_update_schedule(self) -> None:
        schedule = GroupSchedule.objects.create(
            study_group=self.group,
            title="수정 전",
            objective="",
            session_date=timezone.now() + timedelta(days=1),  # 수정됨
            start_time=time(9, 0),
            end_time=time(10, 0),
        )

        url = f"/api/v1/study-groups/{self.group.id}/schedules/{schedule.id}"

        payload = {
            "title": "수정 후",
            "objective": "수정됨",
            "session_date": timezone.now() + timedelta(days=2),
            "start_time": time(13, 0),
            "end_time": time(15, 0),
            "participants": [self.member1.id],
        }

        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schedule.refresh_from_db()
        self.assertEqual(schedule.title, "수정 후")
        self.assertEqual(ScheduleParticipants.objects.count(), 1)

        # 스케줄 삭제

    def test_delete_schedule(self) -> None:
        schedule = GroupSchedule.objects.create(
            study_group=self.group,
            title="삭제 테스트",
            objective="",
            session_date=timezone.now() + timedelta(days=1),
            start_time=time(10, 0),
            end_time=time(11, 0),
        )

        url = f"/api/v1/study-groups/{self.group.id}/schedules/{schedule.id}"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(GroupSchedule.objects.count(), 0)
