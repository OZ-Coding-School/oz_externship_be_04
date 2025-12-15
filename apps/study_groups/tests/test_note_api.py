from datetime import datetime, timedelta
from typing import cast

from django.utils import timezone
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
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=7),
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

    def test_create_note_ignores_invalid_attachments(self) -> None:
        """빈 첨부를 보내면 검증 실패로 400을 돌려준다."""
        self.client.force_authenticate(user=self.user)
        payload = {
            "title": "첨부 없는 노트",
            "content": "내용",
            "attachments": [{"file_url": "", "file_name": ""}],
        }

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(StudyNote.objects.count(), 0)
        self.assertIn("attachments", response.data.get("error_detail", {}))

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

    def test_detail_note_success(self) -> None:
        """멤버는 상세를 볼 수 있고 이미지/첨부가 내려온다."""
        self.client.force_authenticate(user=self.user)
        note = StudyNote.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="노트 상세",
            content="상세 본문",
            ai_summary="요약",
        )
        StudyNoteImage.objects.create(study_note=note, img_url="https://example.com/img1.png")
        StudyNoteAttachment.objects.create(
            study_note=note,
            file_url="https://example.com/file1.pdf",
            file_name="file1.pdf",
        )

        detail_url = f"/api/v1/study-groups/{self.study_group.id}/notes/{note.id}"
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "노트 상세")
        self.assertEqual(response.data["images"][0], "https://example.com/img1.png")
        self.assertEqual(response.data["attachments"][0]["file_name"], "file1.pdf")

    def test_detail_note_forbidden_when_not_member(self) -> None:
        """멤버 아니면 상세 403"""
        other_group = StudyGroup.objects.create(
            name="java",
            introduction="intro",
            max_headcount=3,
            profile_img_url="https://example.com/group2.png",
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=5),
        )
        other_note = StudyNote.objects.create(
            study_group=other_group,
            author=self.other_user,
            title="다른 그룹 노트",
            content="내용",
        )

        self.client.force_authenticate(user=self.user)
        detail_url = f"/api/v1/study-groups/{other_group.id}/notes/{other_note.id}"
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_note_unauthenticated(self) -> None:
        """로그인 없이 상세 조회 시 401"""
        note = StudyNote.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="비로그인",
            content="본문",
        )
        detail_url = f"/api/v1/study-groups/{self.study_group.id}/notes/{note.id}"

        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_note_success(self) -> None:
        """작성자는 노트를 수정할 수 있다."""
        self.client.force_authenticate(user=self.user)
        note = StudyNote.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="초안",
            content="초안 내용",
            ai_summary="요약",
        )
        url = f"/api/v1/study-groups/{self.study_group.id}/notes/{note.id}"
        payload = {
            "title": "수정 제목",
            "content": "수정 내용",
            "images": ["https://example.com/new.png"],
            "attachments": [{"file_url": "https://example.com/new.pdf", "file_name": "new.pdf"}],
        }

        response = self.client.patch(url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertEqual(note.title, "수정 제목")
        self.assertEqual(note.images.count(), 1)
        attachment = cast(StudyNoteAttachment, note.attachments.first())
        self.assertIsNotNone(attachment)
        self.assertEqual(attachment.file_name, "new.pdf")

    def test_patch_note_forbidden_when_not_author(self) -> None:
        """작성자가 아니면 수정 금지"""
        note = StudyNote.objects.create(
            study_group=self.study_group,
            author=self.other_user,
            title="다른 사람 노트",
            content="내용",
        )
        url = f"/api/v1/study-groups/{self.study_group.id}/notes/{note.id}"
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(url, data={"title": "수정"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_note_clear_images_and_attachments(self) -> None:
        """이미지/첨부를 빈 배열로 보내면 모두 삭제된다."""
        self.client.force_authenticate(user=self.user)
        note = StudyNote.objects.create(
            study_group=self.study_group,
            author=self.user,
            title="초안",
            content="내용",
        )
        StudyNoteImage.objects.create(study_note=note, img_url="https://example.com/old.png")
        StudyNoteAttachment.objects.create(
            study_note=note,
            file_url="https://example.com/old.pdf",
            file_name="old.pdf",
        )
        url = f"/api/v1/study-groups/{self.study_group.id}/notes/{note.id}"

        response = self.client.patch(url, data={"images": [], "attachments": []}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        note.refresh_from_db()
        self.assertEqual(note.images.count(), 0)
        self.assertEqual(note.attachments.count(), 0)
