from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import make_aware
from rest_framework.test import APIClient

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models import User

UserModel = get_user_model()


class StudyGroupTests(TestCase):
    user: "User"
    client: APIClient

    def setUp(self) -> None:
        self.user = UserModel.objects.create(
            nickname="member1",
            email="test@example.com",
            birthday=date(2000, 1, 1),
            phone_number="01000000001",
        )
        self.user.set_password("qwer1234")
        self.user.save()

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _dt(self, value: str) -> datetime:
        return make_aware(datetime.fromisoformat(value))

    def test_create_study_group(self) -> None:
        lecture1 = CrawledLecture.objects.create(
            title="강의1",
            instructor="강사1",
            external_id="1",
            average_rating=0.0,
            total_class_time=0,
        )
        lecture2 = CrawledLecture.objects.create(
            title="강의2",
            instructor="강사2",
            external_id="2",
            average_rating=0.0,
            total_class_time=0,
        )

        url = reverse("study-group-list-create")
        data = {
            "name": "알고리즘 스터디",
            "introduction": "코테 대비",
            "max_headcount": 5,
            "start_at": "2026-01-10T00:00:00",
            "end_at": "2026-01-20T00:00:00",
            "lectures": [lecture1.id, lecture2.id],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(StudyGroup.objects.count(), 1)

        study_group = StudyGroup.objects.first()
        assert study_group is not None

        # view에서 리더 자동 생성 test
        self.assertTrue(
            GroupMember.objects.filter(
                study_group_id=study_group.id,
                user_id=self.user.id,
                is_leader=True,
            ).exists()
        )

    def test_list_study_groups(self) -> None:
        StudyGroup.objects.create(
            name="스터디1",
            max_headcount=5,
            start_at=self._dt("2026-01-10T00:00:00"),
            end_at=self._dt("2026-01-20T00:00:00"),
        )

        url = reverse("study-group-list-create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_leave_study_group(self) -> None:
        group = StudyGroup.objects.create(
            name="스터디",
            max_headcount=5,
            start_at=self._dt("2026-01-10T00:00:00"),
            end_at=self._dt("2026-01-20T00:00:00"),
        )

        GroupMember.objects.create(
            study_group_id=group,
            user_id=self.user,
            is_leader=False,
        )

        url = reverse("study-group-leave", args=[group.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            GroupMember.objects.filter(
                study_group_id=group.id,
                user_id=self.user.id,
            ).exists()
        )

    def test_kick_member_forbidden(self) -> None:
        member = UserModel.objects.create(
            email="member@example.com",
            birthday=date(2000, 1, 1),
            phone_number="01000000002",
        )

        group = StudyGroup.objects.create(
            name="스터디",
            max_headcount=5,
            start_at=self._dt("2026-01-10T00:00:00"),
            end_at=self._dt("2026-01-20T00:00:00"),
        )

        GroupMember.objects.create(
            study_group_id=group,
            user_id=self.user,
            is_leader=False,
        )
        GroupMember.objects.create(
            study_group_id=group,
            user_id=member,
            is_leader=False,
        )

        url = reverse("study-group-kick", args=[group.id, member.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)

    def test_kick_member_success(self) -> None:
        member = UserModel.objects.create(
            email="member2@example.com",
            birthday=date(2000, 1, 1),
            nickname="member2",
            phone_number="01000000003",
        )

        group = StudyGroup.objects.create(
            name="스터디",
            max_headcount=5,
            start_at=self._dt("2026-01-10T00:00:00"),
            end_at=self._dt("2026-01-20T00:00:00"),
        )

        GroupMember.objects.create(
            study_group_id=group,
            user_id=self.user,
            is_leader=True,
        )
        GroupMember.objects.create(
            study_group_id=group,
            user_id=member,
            is_leader=False,
        )

        url = reverse("study-group-kick", args=[group.id, member.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            GroupMember.objects.filter(
                study_group_id=group.id,
                user_id=member.id,
            ).exists()
        )


### 추가 필요한 부분 (주로 권한 관련 - 비로그인유저 / 일반로그인유저 / 리더로그인유저)
# 리더 탈퇴 실패 테스트
# test_leader_leave
# # 리더만 수정/삭제 가능 여부 테스트
# test_leader_update
# # 리더 위임 테스트
# test_leader_retrieve
