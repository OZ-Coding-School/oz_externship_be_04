from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import StudyGroup, StudyLecture
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

    def test_update_study_group_lectures_replaces_all(self) -> None:
        """lectures 필드를 보내면 기존 강의 매핑을 모두 갈아준다."""
        first = CrawledLecture.objects.create(
            external_id=1,
            title="old",
            instructor="old",
            average_rating=4.5,
            total_class_time=10,
            difficulty="EASY",
            description="desc",
            platform="INFLEARN",
            original_price=1000,
            discount_price=900,
            url_link="https://example.com/old",
            thumbnail_img_url="https://example.com/old.png",
        )
        second = CrawledLecture.objects.create(
            external_id=2,
            title="new",
            instructor="new",
            average_rating=4.0,
            total_class_time=8,
            difficulty="EASY",
            description="desc",
            platform="INFLEARN",
            original_price=2000,
            discount_price=1800,
            url_link="https://example.com/new",
            thumbnail_img_url="https://example.com/new.png",
        )
        group = StudyGroup.objects.create(**self._make_payload("lecture-replace"))
        StudyLecture.objects.create(study_group=group, lecture=first)

        payload = {"lectures": [second.id]}
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f"{self.base_url}/{group.id}/update", data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(StudyLecture.objects.filter(study_group=group).count(), 1)
        self.assertEqual(StudyLecture.objects.get(study_group=group).lecture_id, second.id)

    def test_delete_study_group(self) -> None:
        group = StudyGroup.objects.create(**self._make_payload("delete-target"))

        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"{self.base_url}/{group.id}/delete")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(StudyGroup.objects.filter(id=group.id).exists())

    def test_create_study_group_with_lectures(self) -> None:
        """강의 id를 보내면 StudyLecture가 생성된다."""
        lecture1 = CrawledLecture.objects.create(
            external_id=101,
            title="lec1",
            instructor="t1",
            average_rating=4.5,
            total_class_time=12,
            difficulty="EASY",
            description="desc",
            platform="INFLEARN",
            original_price=1000,
            discount_price=800,
            url_link="https://example.com/lec1",
            thumbnail_img_url="https://example.com/lec1.png",
        )
        lecture2 = CrawledLecture.objects.create(
            external_id=102,
            title="lec2",
            instructor="t2",
            average_rating=4.0,
            total_class_time=10,
            difficulty="EASY",
            description="desc",
            platform="INFLEARN",
            original_price=1000,
            discount_price=800,
            url_link="https://example.com/lec2",
            thumbnail_img_url="https://example.com/lec2.png",
        )
        payload = self._make_payload("with-lectures")
        payload["lectures"] = [lecture1.id, lecture2.id]

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"{self.base_url}/create", data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(StudyLecture.objects.count(), 2)

    def test_create_study_group_rejects_past_start(self) -> None:
        """시작일이 과거면 400을 반환한다."""
        payload = self._make_payload("past")
        payload["start_at"] = (timezone.now() - timedelta(days=1)).isoformat()

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"{self.base_url}/create", data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("start_at", response.data.get("error_detail", {}))

    def test_create_study_group_rejects_short_duration(self) -> None:
        """종료일이 시작일보다 5일 미만이면 400."""
        payload = self._make_payload("short")
        now = timezone.now()
        payload["start_at"] = now.isoformat()
        payload["end_at"] = (now + timedelta(days=2)).isoformat()

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"{self.base_url}/create", data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_at", response.data.get("error_detail", {}))

    def test_create_study_group_rejects_too_many_lectures(self) -> None:
        """강의가 5개 초과면 400."""
        payload = self._make_payload("too-many")
        payload["lectures"] = [1, 2, 3, 4, 5, 6]

        self.client.force_authenticate(user=self.user)
        response = self.client.post(f"{self.base_url}/create", data=payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("lectures", response.data.get("error_detail", {}))
