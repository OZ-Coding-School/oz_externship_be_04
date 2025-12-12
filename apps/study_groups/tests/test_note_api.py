from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.test import APITestCase

from apps.study_groups.models import (
    GroupMember,
    StudyGroup,
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.users.models import User


class StudyNoteAPITest(APITestCase):
    def setUp(self) -> None:
        # 기본 유저와 스터디 그룹을 만든다.
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass1234",
            name="tester",
            nickname="tester",
            phone_number="01012345678",
            gender="M",
            birthday=datetime.now().date(),
            profile_img_url="https://example.com/profile.png",
            is_active=True,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="pass1234",
            name="other",
            nickname="other",
            phone_number="01012345679",
            gender="F",
            birthday=datetime.now().date(),
            profile_img_url="https://example.com/profile2.png",
            is_active=True,
        )
        self.study_group = StudyGroup.objects.create(
            name="python",
            introduction="intro",
            max_headcount=5,
            profile_img_url="https://example.com/group.png",
            start_at=datetime.now(),
            end_at=datetime.now() + timedelta(days=7),
        )
        GroupMember.objects.create(study_group_id=self.study_group, user_id=self.user, is_leader=True)
        self.url = f"/api/v1/study-groups/{self.study_group.id}/notes"

    def test_create_note_success(self) -> None:
        """멤버가 제목/내용/이미지/첨부까지 넣으면 201이 난다."""
        self.client.force_authenticate(user=self.user)
        payload = {
            "title": "첫 노트",
            "content": "내용 본문",
            "images": ["https://example.com/img1.png", "https://example.com/img2.png"],
            "attachments": [
                {"file_url": "https://example.com/file1.pdf", "file_name": "file1.pdf"},
            ],
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(StudyNote.objects.filter(title="첫 노트").exists())
        self.assertEqual(StudyNoteImage.objects.count(), 2)
        self.assertEqual(StudyNoteAttachment.objects.count(), 1)

    def test_create_note_forbidden_when_not_member(self) -> None:
        """멤버가 아니면 403"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(self.url, data={"title": "x", "content": "y"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_note_unauthenticated(self) -> None:
        """로그인 안 하면 401"""
        response = self.client.post(self.url, data={"title": "x", "content": "y"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_notes_success(self) -> None:
        """멤버는 목록을 볼 수 있고 썸네일은 첫 이미지다."""
        self.client.force_authenticate(user=self.user)
        note = StudyNote.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="노트1",
            content="본문",
        )
        StudyNoteImage.objects.create(study_note=note, img_url="https://example.com/img-thumb.png")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        first_item = response.data["results"][0]
        self.assertEqual(first_item["title"], "노트1")
        self.assertEqual(first_item["thumbnail"], "https://example.com/img-thumb.png")

    def test_list_notes_forbidden_when_not_member(self) -> None:
        """멤버가 아니면 조회도 403"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_notes_group_not_found(self) -> None:
        """없는 그룹이면 404"""
        self.client.force_authenticate(user=self.user)
        missing_url = "/api/v1/study-groups/999/notes"

        response = self.client.get(missing_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
