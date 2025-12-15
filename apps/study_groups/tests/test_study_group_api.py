from datetime import timedelta
from typing import Any

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import StudyGroup, StudyLecture
from apps.study_groups.serializers.study_group import StudyGroupSerializer
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

    def _make_payload(self, name: str = "python") -> dict[str, Any]:
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

    def test_retrieve_study_group_not_found(self) -> None:
        response = self.client.get(f"{self.base_url}/9999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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

    def test_delete_study_group_not_found(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"{self.base_url}/9999/delete")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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

    def test_list_study_groups_is_leader_flag(self) -> None:
        """목록에서 is_leader, member_count를 포함한다."""
        group = StudyGroup.objects.create(**self._make_payload("leader"))
        # 현재 테스트 유저를 리더로 추가
        from apps.study_groups.models import GroupMember

        GroupMember.objects.create(study_group_id=group, user_id=self.user, is_leader=True)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.base_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["is_leader"], True)
        self.assertIn("member_count", response.data[0])

    def test_list_study_groups_no_status_param(self) -> None:
        """status 파라미터 없이도 목록이 내려온다."""
        StudyGroup.objects.create(**self._make_payload("nostatus"))

        response = self.client.get(self.base_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_study_group_serializer_end_at_validation(self) -> None:
        """종료일 5일 미만이면 시리얼라이저가 400을 낸다."""
        now = timezone.now()
        serializer = StudyGroupSerializer(
            data={
                "name": "s1",
                "introduction": "i",
                "max_headcount": 3,
                "profile_img_url": "https://x.com/g.png",
                "start_at": now.isoformat(),
                "end_at": (now + timedelta(days=2)).isoformat(),
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("end_at", serializer.errors)

    def test_study_group_serializer_past_start(self) -> None:
        """시작일이 과거면 400"""
        past = timezone.now() - timedelta(days=1)
        future = timezone.now() + timedelta(days=6)
        serializer = StudyGroupSerializer(
            data={
                "name": "s2",
                "introduction": "i2",
                "max_headcount": 3,
                "profile_img_url": "https://x.com/g2.png",
                "start_at": past.isoformat(),
                "end_at": future.isoformat(),
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("start_at", serializer.errors)

    def test_serializer_create_with_lectures(self) -> None:
        """시리얼라이저 create도 StudyLecture를 만든다."""
        lecture = CrawledLecture.objects.create(
            external_id=201,
            title="c1",
            instructor="i1",
            average_rating=4.5,
            total_class_time=10,
            difficulty="EASY",
            description="d",
            platform="INFLEARN",
            original_price=1000,
            discount_price=900,
            url_link="https://x.com/c1",
            thumbnail_img_url="https://x.com/c1.png",
        )
        data = self._make_payload("serializer")
        data["lectures"] = [lecture.id]
        serializer = StudyGroupSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.assertEqual(StudyLecture.objects.count(), 1)

    def test_serializer_update_replaces_lectures(self) -> None:
        """update 분기 커버: 기존 강의를 교체한다."""
        lec1 = CrawledLecture.objects.create(
            external_id=301,
            title="c2",
            instructor="i2",
            average_rating=4.0,
            total_class_time=9,
            difficulty="EASY",
            description="d",
            platform="INFLEARN",
            original_price=1000,
            discount_price=900,
            url_link="https://x.com/c2",
            thumbnail_img_url="https://x.com/c2.png",
        )
        lec2 = CrawledLecture.objects.create(
            external_id=302,
            title="c3",
            instructor="i3",
            average_rating=4.0,
            total_class_time=9,
            difficulty="EASY",
            description="d",
            platform="INFLEARN",
            original_price=1000,
            discount_price=900,
            url_link="https://x.com/c3",
            thumbnail_img_url="https://x.com/c3.png",
        )
        group = StudyGroup.objects.create(**self._make_payload("update-serializer"))
        StudyLecture.objects.create(study_group=group, lecture=lec1)

        serializer = StudyGroupSerializer(instance=group, data={"lectures": [lec2.id]}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.assertEqual(StudyLecture.objects.filter(study_group=group).count(), 1)
        self.assertEqual(StudyLecture.objects.get(study_group=group).lecture_id, lec2.id)
