from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.study_groups.models import GroupMember, StudyGroup, StudyNote
from apps.users.models import User


class StudyGroupSmokeTest(APITestCase):
    """기존 tests.py에 있던 기본 커버리지 테스트를 패키지로 이동."""

    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="u1@example.com",
            password="1234",
            name="u1",
            nickname="u1",
            phone_number="01000000000",
            gender="M",
            birthday=timezone.now().date(),
            profile_img_url="https://x.com/u.png",
            is_active=True,
        )
        self.group = StudyGroup.objects.create(
            name="g1",
            introduction="i1",
            max_headcount=3,
            profile_img_url="https://x.com/g.png",
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=7),
        )
        GroupMember.objects.create(study_group_id=self.group, user_id=self.user, is_leader=True)
        self.note = StudyNote.objects.create(study_group=self.group, author=self.user, title="t1", content="c1")

    def test_note_list_success(self) -> None:
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/v1/study-groups/{self.group.id}/notes")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_note_detail_404(self) -> None:
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/v1/study-groups/{self.group.id}/notes/9999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_group_list_filter(self) -> None:
        StudyGroup.objects.create(
            name="g2",
            introduction="i2",
            max_headcount=4,
            profile_img_url="https://x.com/g2.png",
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=7),
            status="ONGOING",
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/v1/study-groups?status=ONGOING")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_group_create_missing_name(self) -> None:
        self.client.force_authenticate(user=self.user)
        payload = {
            "introduction": "i3",
            "max_headcount": 3,
            "profile_img_url": "https://x.com/g3.png",
            "start_at": timezone.now().isoformat(),
            "end_at": (timezone.now() + timedelta(days=7)).isoformat(),
        }
        resp = self.client.post("/api/v1/study-groups/create", data=payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_group_detail_404(self) -> None:
        self.client.force_authenticate(user=self.user)
        resp = self.client.get("/api/v1/study-groups/9999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_group_update_without_lectures(self) -> None:
        """lectures를 안 보내면 기존 매핑을 유지한 채 필드만 수정된다."""
        group = StudyGroup.objects.create(
            name="upd1",
            introduction="old",
            max_headcount=3,
            profile_img_url="https://x.com/g4.png",
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=7),
        )
        self.client.force_authenticate(user=self.user)
        resp = self.client.patch(
            f"/api/v1/study-groups/{group.id}/update",
            data={"introduction": "new"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        group.refresh_from_db()
        self.assertEqual(group.introduction, "new")

    def test_note_list_pagination_param(self) -> None:
        """page_size 파라미터가 있어도 목록이 응답된다."""
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(f"/api/v1/study-groups/{self.group.id}/notes?page_size=5")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
