from datetime import datetime, timedelta
from typing import cast

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from apps.study_groups.models import (
    GroupMember,
    StudyGroup,
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.study_groups.serializers import (
    StudyNoteCreateSerializer,
    StudyNoteDetailSerializer,
    StudyNoteListSerializer,
)
from apps.study_groups.views import StudyNoteAPIView, StudyNoteDetailAPIView
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

    def test_create_note_group_not_found(self) -> None:
        """없는 그룹이면 404"""
        self.client.force_authenticate(user=self.user)
        missing_url = "/api/v1/study-groups/9999/notes"

        response = self.client.post(missing_url, data={"title": "x", "content": "y"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_note_blank_fields(self) -> None:
        """제목/내용이 공백이면 400"""
        self.client.force_authenticate(user=self.user)
        payload = {"title": "", "content": ""}

        response = self.client.post(self.url, data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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

    def test_detail_note_not_found(self) -> None:
        """없는 노트면 404"""
        self.client.force_authenticate(user=self.user)
        url = f"/api/v1/study-groups/{self.study_group.id}/notes/9999"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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

    def test_patch_note_not_found(self) -> None:
        """없는 노트 수정 시 404"""
        self.client.force_authenticate(user=self.user)
        url = f"/api/v1/study-groups/{self.study_group.id}/notes/9999"

        response = self.client.patch(url, data={"title": "t"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class StudyNoteSerializerTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="s1@example.com",
            password="1234",
            name="u1",
            nickname="u1",
            phone_number="01011112222",
            gender="M",
            birthday=datetime.now().date(),
            profile_img_url="https://x.com/a.png",
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

    def test_create_serializer_creates_related(self) -> None:
        serializer = StudyNoteCreateSerializer(
            data={
                "title": "t1",
                "content": "c1",
                "images": ["https://x.com/i.png"],
                "attachments": [{"file_url": "https://x.com/f.pdf", "file_name": "f.pdf"}],
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save(author=self.user, study_group=self.group)

        self.assertEqual(StudyNote.objects.count(), 1)
        note = StudyNote.objects.first()
        self.assertIsNotNone(note)
        assert note is not None
        self.assertEqual(note.images.count(), 1)
        self.assertEqual(note.attachments.count(), 1)

    def test_list_serializer_thumbnail_none(self) -> None:
        note = StudyNote.objects.create(study_group=self.group, author=self.user, title="t1", content="c1")

        serializer = StudyNoteListSerializer(instance=note)

        self.assertIsNone(serializer.data["thumbnail"])

    def test_detail_serializer_returns_attachments(self) -> None:
        note = StudyNote.objects.create(study_group=self.group, author=self.user, title="t1", content="c1")
        StudyNoteAttachment.objects.create(study_note=note, file_url="https://x.com/f.pdf", file_name="f.pdf")

        serializer = StudyNoteDetailSerializer(instance=note)

        self.assertEqual(serializer.data["attachments"][0]["file_name"], "f.pdf")

    def test_create_serializer_skips_invalid_attachment(self) -> None:
        serializer = StudyNoteCreateSerializer(
            data={
                "title": "t2",
                "content": "c2",
                "attachments": [{"file_url": "https://x.com/only-url"}],
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save(author=self.user, study_group=self.group)

        note = StudyNote.objects.first()
        assert note is not None
        self.assertEqual(note.attachments.count(), 0)

    def test_detail_serializer_images(self) -> None:
        note = StudyNote.objects.create(study_group=self.group, author=self.user, title="t3", content="c3")
        StudyNoteImage.objects.create(study_note=note, img_url="https://x.com/img.png")

        serializer = StudyNoteDetailSerializer(instance=note)

        self.assertEqual(serializer.data["images"][0], "https://x.com/img.png")

    def test_create_serializer_invalid_images_type(self) -> None:
        """images가 리스트가 아니면 400"""
        serializer = StudyNoteCreateSerializer(
            data={
                "title": "bad",
                "content": "c",
                "images": "not-a-list",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("images", serializer.errors)


class StudyNoteViewUnitTest(APITestCase):
    # 뷰 단위 경로를 직접 호출해 분기 커버리지를 확인한다.
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email="v1@example.com",
            password="1234",
            name="v1",
            nickname="v1",
            phone_number="01033334444",
            gender="M",
            birthday=datetime.now().date(),
            profile_img_url="https://x.com/u.png",
            is_active=True,
        )
        self.group = StudyGroup.objects.create(
            name="vgroup",
            introduction="i1",
            max_headcount=3,
            profile_img_url="https://x.com/g.png",
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=7),
        )
        GroupMember.objects.create(study_group_id=self.group, user_id=self.user, is_leader=True)

    def test_view_get_list_executes(self) -> None:
        request = self.factory.get(f"/api/v1/study-groups/{self.group.id}/notes")
        force_authenticate(request, user=self.user)
        response = StudyNoteAPIView.as_view()(request, study_group_id=self.group.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_post_executes(self) -> None:
        payload = {"title": "t1", "content": "c1"}
        request = self.factory.post(
            f"/api/v1/study-groups/{self.group.id}/notes", data=payload, content_type="application/json"
        )
        force_authenticate(request, user=self.user)
        response = StudyNoteAPIView.as_view()(request, study_group_id=self.group.id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_view_detail_get_executes(self) -> None:
        note = StudyNote.objects.create(study_group=self.group, author=self.user, title="t1", content="c1")
        request = self.factory.get(f"/api/v1/study-groups/{self.group.id}/notes/{note.id}")
        force_authenticate(request, user=self.user)
        response = StudyNoteDetailAPIView.as_view()(request, study_group_id=self.group.id, note_id=note.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_detail_patch_executes(self) -> None:
        note = StudyNote.objects.create(study_group=self.group, author=self.user, title="t1", content="c1")
        payload = {"title": "t2", "content": "c2"}
        request = self.factory.patch(
            f"/api/v1/study-groups/{self.group.id}/notes/{note.id}", data=payload, content_type="application/json"
        )
        force_authenticate(request, user=self.user)
        response = StudyNoteDetailAPIView.as_view()(request, study_group_id=self.group.id, note_id=note.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
