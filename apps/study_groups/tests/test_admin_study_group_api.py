from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import GroupMember, StudyGroup, StudyLecture

User = get_user_model()


class AdminStudyGroupAPITest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        # 일반 유저
        self.user = User.objects.create_user(
            nickname="user_1",
            email="normal_user@example.com",
            phone_number="01000001000",
        )

        # 관리자(스태프) 유저 - 현재 admin 조건: is_staff OR is_superuser
        self.admin = User.objects.create_user(
            nickname="admin_user",
            email="admin_user@example.com",
            phone_number="01000002000",
            is_staff=True,
            is_active=True,
        )

        now = timezone.now()

        # 테스트용 강의 생성
        self.lecture1 = CrawledLecture.objects.create(
            title="파이썬 기초",
            instructor="강사1",
            external_id="1",
            average_rating=4.5,
            total_class_time=100,
            difficulty="EASY",
            description="파이썬 기초 강의",
            platform="INFLEARN",
            url_link="https://example.com/lecture1",
            thumbnail_img_url="https://example.com/thumb1.jpg",
        )

        self.lecture2 = CrawledLecture.objects.create(
            title="장고 심화",
            instructor="강사2",
            external_id="2",
            average_rating=4.8,
            total_class_time=200,
            difficulty="HARD",
            description="장고 심화 강의",
            platform="INFLEARN",
            url_link="https://example.com/lecture2",
            thumbnail_img_url="https://example.com/thumb2.jpg",
        )

        # 스터디 그룹 생성
        self.study_group1 = StudyGroup.objects.create(
            name="파이썬 스터디",
            introduction="파이썬 깨부실분들 구합니다.",
            max_headcount=5,
            start_at=now,
            end_at=now + timedelta(days=7),
            status=StudyGroup.StudyGroupStatusChoices.PENDING,
        )

        self.study_group2 = StudyGroup.objects.create(
            name="장고 스터디",
            introduction="DRF 집중",
            max_headcount=5,
            start_at=now,
            end_at=now + timedelta(days=7),
            status=StudyGroup.StudyGroupStatusChoices.ONGOING,
        )

        self.study_group3 = StudyGroup.objects.create(
            name="알고리즘 스터디",
            introduction="코테 대비",
            max_headcount=10,
            start_at=now - timedelta(days=30),
            end_at=now - timedelta(days=1),
            status=StudyGroup.StudyGroupStatusChoices.ENDED,
        )

        # 강의 연결
        StudyLecture.objects.create(study_group=self.study_group1, lecture=self.lecture1)
        StudyLecture.objects.create(study_group=self.study_group2, lecture=self.lecture2)

        # 멤버 추가
        GroupMember.objects.create(
            study_group_id=self.study_group1,
            user_id=self.admin,
            is_leader=True,
        )
        GroupMember.objects.create(
            study_group_id=self.study_group1,
            user_id=self.user,
            is_leader=False,
        )

    def _auth(self, user: Any) -> None:
        self.client.force_authenticate(user=user)
        self.client.force_login(user=user)

    # -------------------------
    # List API: GET /admin/study-groups
    # -------------------------

    def test_admin_study_group_list_success_200(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-group-list")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)
        self.assertEqual(len(res.data), 3)

        # 필드 검증
        item = res.data[0]
        self.assertIn("id", item)
        self.assertIn("name", item)
        self.assertIn("introduction", item)
        self.assertIn("max_headcount", item)
        self.assertIn("current_headcount", item)
        self.assertIn("profile_img_url", item)
        self.assertIn("start_at", item)
        self.assertIn("end_at", item)
        self.assertIn("status", item)
        self.assertIn("created_at", item)
        self.assertIn("updated_at", item)
        self.assertIn("lectures", item)
        self.assertIn("leader", item)

    def test_admin_study_group_list_unauthenticated_401(self) -> None:
        self.client.logout()

        url = reverse("admin-study-group-list")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 401)

    def test_admin_study_group_list_forbidden_if_not_admin_403(self) -> None:
        self._auth(self.user)

        url = reverse("admin-study-group-list")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "권한이 없습니다."})

    def test_admin_study_group_list_search_filters_by_name(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-group-list")

        # "파이썬" 검색
        res = self.client.get(url, data={"search": "파이썬"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "파이썬 스터디")

        # "장고" 검색
        res = self.client.get(url, data={"search": "장고"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "장고 스터디")

    def test_admin_study_group_list_filter_by_status_pending(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-group-list")

        res = self.client.get(url, data={"status": "PENDING"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["status"], "PENDING")
        self.assertEqual(res.data[0]["name"], "파이썬 스터디")

    def test_admin_study_group_list_filter_by_status_ongoing(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-group-list")

        res = self.client.get(url, data={"status": "ONGOING"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["status"], "ONGOING")
        self.assertEqual(res.data[0]["name"], "장고 스터디")

    def test_admin_study_group_list_filter_by_status_ended(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-group-list")

        res = self.client.get(url, data={"status": "ENDED"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["status"], "ENDED")
        self.assertEqual(res.data[0]["name"], "알고리즘 스터디")

    def test_admin_study_group_list_search_and_status_filter_combined(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-group-list")

        # "스터디" 검색 + PENDING 필터
        res = self.client.get(url, data={"search": "스터디", "status": "PENDING"})

        self.assertEqual(res.status_code, 200)
        # "파이썬 스터디"만 매칭
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], "파이썬 스터디")
        self.assertEqual(res.data[0]["status"], "PENDING")

    # -------------------------
    # Detail API: GET /admin/study-groups/{study_group_id}
    # -------------------------

    def test_admin_study_group_detail_success_200(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-group-detail", kwargs={"study_group_id": self.study_group1.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["id"], self.study_group1.id)
        self.assertEqual(res.data["name"], "파이썬 스터디")

        # 필드 검증
        self.assertIn("id", res.data)
        self.assertIn("name", res.data)
        self.assertIn("introduction", res.data)
        self.assertIn("max_headcount", res.data)
        self.assertIn("current_headcount", res.data)
        self.assertIn("profile_img_url", res.data)
        self.assertIn("start_at", res.data)
        self.assertIn("end_at", res.data)
        self.assertIn("status", res.data)
        self.assertIn("created_at", res.data)
        self.assertIn("updated_at", res.data)
        self.assertIn("lectures", res.data)
        self.assertIn("members", res.data)
        self.assertIn("reviews", res.data)

        # nested 검증
        self.assertIsInstance(res.data["lectures"], list)
        if res.data["lectures"]:
            self.assertIn("id", res.data["lectures"][0])
            self.assertIn("title", res.data["lectures"][0])

        self.assertIsInstance(res.data["members"], list)
        if res.data["members"]:
            self.assertIn("id", res.data["members"][0])
            self.assertIn("nickname", res.data["members"][0])
            self.assertIn("email", res.data["members"][0])
            self.assertIn("is_leader", res.data["members"][0])

        self.assertIsInstance(res.data["reviews"], list)

    def test_admin_study_group_detail_unauthenticated_401(self) -> None:
        self.client.logout()

        url = reverse("admin-study-group-detail", kwargs={"study_group_id": self.study_group1.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 401)

    def test_admin_study_group_detail_forbidden_if_not_admin_403(self) -> None:
        self._auth(self.user)

        url = reverse("admin-study-group-detail", kwargs={"study_group_id": self.study_group1.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "권한이 없습니다."})

    def test_admin_study_group_detail_not_found_404(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-group-detail", kwargs={"study_group_id": 999999})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, {"error_detail": "해당 스터디 그룹을 찾을 수 없습니다."})
