from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.study_groups.models import GroupMember, StudyGroup, StudyNote

User = get_user_model()


class StudyNoteCreateAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="test@example.com",
            name="tester",
            nickname="tester",
            phone_number="+8201000000000",
            gender="M",
            birthday=timezone.now().date(),
            profile_img_url="http://example.com/profile.png",
        )
        self.user.set_password("password123")
        self.user.save()
        self.study_group = StudyGroup.objects.create(
            name="파이썬 스터디",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )
        GroupMember.objects.create(study_group=self.study_group, user=self.user)
        self.url = reverse("study-note-create", kwargs={"study_group_id": self.study_group.id})

    def test_create_note_success(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            "title": "첫 노트",
            "content": "내용입니다. 임시 요약에 쓰일 본문입니다.",
            "images": ["http://example.com/img.png"],
            "attachments": [{"file_url": "http://example.com/file.pdf"}],
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StudyNote.objects.count(), 1)
        note = StudyNote.objects.first()
        self.assertEqual(note.ai_summary, "TODO: AI 요약")
        self.assertEqual(len(note.images.all()), 1)
        self.assertEqual(len(note.attachments.all()), 1)
        self.assertEqual(response.data["id"], note.id)
        self.assertEqual(response.data["ai_summary"], "TODO: AI 요약")

    def test_create_note_unauthenticated(self):
        payload = {
            "title": "첫 노트",
            "content": "내용입니다.",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_note_invalid_group(self):
        self.client.force_authenticate(user=self.user)
        bad_url = reverse("study-note-create", kwargs={"study_group_id": 999999})
        payload = {
            "title": "첫 노트",
            "content": "내용입니다.",
        }

        response = self.client.post(bad_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_note_when_not_group_member(self):
        other_user = User.objects.create(
            email="other@example.com",
            name="other",
            nickname="other",
            phone_number="+8201000000001",
            gender="M",
            birthday=timezone.now().date(),
            profile_img_url="http://example.com/profile2.png",
        )
        other_user.set_password("password123")
        other_user.save()
        self.client.force_authenticate(user=other_user)

        payload = {"title": "첫 노트", "content": "내용입니다."}

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(StudyNote.objects.count(), 0)
