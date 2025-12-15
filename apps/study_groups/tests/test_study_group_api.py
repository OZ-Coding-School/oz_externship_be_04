from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.study_groups.models import StudyGroup
from apps.users.models import User


class StudyGroupAPITest(APITestCase):
    def setUp(self) -> None:
        self.base_url = "/api/v1/study-groups"
        self.user = User.objects.create_user(
            email="group@example.com",
            password="pass1234",
            name="group",
            nickname="group",
            phone_number="01099998888",
            gender="M",
            birthday=timezone.now().date(),
            profile_img_url="https://example.com/u.png",
            is_active=True,
        )

    def _make_payload(self, name: str = "python") -> dict:
        now = timezone.now()
        return {
            "name": name,
            "introduction": "intro",
            "max_headcount": 5,
            "profile_img_url": "https://example.com/group.png",
            "start_at": now.isoformat(),
            "end_at": (now + timedelta(days=7)).isoformat(),
        }

    def test_create_study_group(self) -> None:
        payload = self._make_payload("django")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"{self.base_url}/create", data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(StudyGroup.objects.filter(name="django").exists())

    def test_list_study_groups_with_status_filter(self) -> None:
        StudyGroup.objects.create(**self._make_payload("pending"))
        StudyGroup.objects.create(**self._make_payload("ongoing"), status="ONGOING")

        response = self.client.get(f"{self.base_url}?status=ONGOING")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "ongoing")

    def test_retrieve_study_group(self) -> None:
        group = StudyGroup.objects.create(**self._make_payload("detail"))

        response = self.client.get(f"{self.base_url}/{group.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "detail")

    def test_update_study_group(self) -> None:
        group = StudyGroup.objects.create(**self._make_payload("patch-target"))
        payload = {"introduction": "updated"}

        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"{self.base_url}/{group.id}/update", data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        group.refresh_from_db()
        self.assertEqual(group.introduction, "updated")

    def test_delete_study_group(self) -> None:
        group = StudyGroup.objects.create(**self._make_payload("delete-target"))

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"{self.base_url}/{group.id}/delete")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(StudyGroup.objects.filter(id=group.id).exists())
