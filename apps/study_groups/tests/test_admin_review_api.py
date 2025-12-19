from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.study_groups.models import Review, StudyGroup

User = get_user_model()


class AdminStudyReviewAPITest(APITestCase):
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
            status=StudyGroup.StudyGroupStatusChoices.PENDING,
        )

        # 리뷰 3개 생성 (search/sort/pagination 테스트용)
        self.r1 = Review.objects.create(
            user=self.user, study_group=self.study_group1, star_rating=5, content="test alpha"
        )
        self.r2 = Review.objects.create(
            user=self.admin, study_group=self.study_group1, star_rating=3, content="beta content"
        )
        self.r3 = Review.objects.create(
            user=self.user, study_group=self.study_group2, star_rating=4, content="gamma test"
        )

    def _auth(self, user: Any) -> None:
        self.client.force_authenticate(user=user)
        self.client.force_login(user=user)

    # -------------------------
    # Detail API: GET /admin/study-reviews/{review_id}
    # -------------------------

    def test_admin_review_detail_success_200(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-review-detail", kwargs={"review_id": self.r1.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["id"], self.r1.id)

        # 필드 검증
        self.assertIn("study_group", res.data)
        self.assertIn("author", res.data)
        self.assertIn("star_rating", res.data)
        self.assertIn("content", res.data)
        self.assertIn("created_at", res.data)
        self.assertIn("updated_at", res.data)

        # nested 검증
        self.assertIn("id", res.data["study_group"])
        self.assertIn("name", res.data["study_group"])
        self.assertIn("start_at", res.data["study_group"])
        self.assertIn("end_at", res.data["study_group"])
        self.assertIn("introduction", res.data["study_group"])

        self.assertIn("id", res.data["author"])
        self.assertIn("nickname", res.data["author"])
        self.assertIn("email", res.data["author"])

    def test_admin_review_detail_unauthenticated_401(self) -> None:
        self.client.logout()

        url = reverse("admin-study-review-detail", kwargs={"review_id": self.r1.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."})

    def test_admin_review_detail_forbidden_if_not_admin_403(self) -> None:
        self._auth(self.user)

        url = reverse("admin-study-review-detail", kwargs={"review_id": self.r1.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "권한이 없습니다."})

    def test_admin_review_detail_not_found_404(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-review-detail", kwargs={"review_id": 999999})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, {"error_detail": "스터디 리뷰를 찾을 수 없습니다."})

    def test_admin_review_detail_internal_error_500(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-review-detail", kwargs={"review_id": self.r1.id})

        with patch(
            "apps.study_groups.views.admin_review_view.Review.objects.select_related", side_effect=Exception("boom")
        ):
            res = self.client.get(url)

        self.assertEqual(res.status_code, 500)
        self.assertEqual(res.data, {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."})

    # -------------------------
    # List API: GET /admin/study-reviews
    # -------------------------

    def test_admin_review_list_success_200_basic_shape(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-review-list")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertIn("count", res.data)
        self.assertIn("next", res.data)
        self.assertIn("previous", res.data)
        self.assertIn("results", res.data)

        self.assertIsInstance(res.data["results"], list)
        self.assertEqual(res.data["count"], 3)

        # results 아이템 구조 검증
        item = res.data["results"][0]
        self.assertIn("id", item)
        self.assertIn("study_group", item)
        self.assertIn("author", item)
        self.assertIn("star_rating", item)
        self.assertIn("content", item)
        self.assertIn("created_at", item)
        self.assertIn("updated_at", item)

        self.assertIn("id", item["study_group"])
        self.assertIn("name", item["study_group"])

        self.assertIn("id", item["author"])
        self.assertIn("nickname", item["author"])
        self.assertIn("email", item["author"])

    def test_admin_review_list_unauthenticated_401(self) -> None:
        self.client.logout()

        url = reverse("admin-study-review-list")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."})

    def test_admin_review_list_forbidden_if_not_admin_403(self) -> None:
        self._auth(self.user)

        url = reverse("admin-study-review-list")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "권한이 없습니다."})

    def test_admin_review_list_sort_latest_default(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-review-list")
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

        # 기본 latest: created_at desc, id desc
        ids = [x["id"] for x in res.data["results"]]
        expected = list(Review.objects.order_by("-created_at", "-id").values_list("id", flat=True))
        self.assertEqual(ids, expected)

    def test_admin_review_list_sort_oldest(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-review-list")
        res = self.client.get(url, data={"sort": "oldest"})

        self.assertEqual(res.status_code, 200)

        ids = [x["id"] for x in res.data["results"]]
        expected = list(Review.objects.order_by("created_at", "id").values_list("id", flat=True))
        self.assertEqual(ids, expected)

    def test_admin_review_list_search_filters_results(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-review-list")

        # "test"가 포함된 content: r1, r3
        res = self.client.get(url, data={"search": "test"})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 2)
        got_ids = sorted([x["id"] for x in res.data["results"]])
        self.assertEqual(got_ids, sorted([self.r1.id, self.r3.id]))

    def test_admin_review_list_pagination_page_and_page_size(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-review-list")

        # page_size=2이면 3개 중 2개만 내려오고 next가 생겨야 함
        res = self.client.get(url, data={"page": 1, "page_size": 2})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 3)
        self.assertEqual(len(res.data["results"]), 2)
        self.assertIsNotNone(res.data["next"])
        self.assertIsNone(res.data["previous"])

        # next url에 page=2 & page_size=2 포함되는지 (정확한 도메인은 testserver)
        self.assertIn("page=2", res.data["next"])
        self.assertIn("page_size=2", res.data["next"])

        # 2페이지는 1개만 내려오고 previous가 생겨야 함
        res2 = self.client.get(url, data={"page": 2, "page_size": 2})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(len(res2.data["results"]), 1)
        self.assertIsNone(res2.data["next"])
        self.assertIsNotNone(res2.data["previous"])
        self.assertIn("page=1", res2.data["previous"])

    def test_admin_review_list_internal_error_500(self) -> None:
        self._auth(self.admin)

        url = reverse("admin-study-review-list")

        with patch(
            "apps.study_groups.views.admin_review_view.Review.objects.select_related", side_effect=Exception("boom")
        ):
            res = self.client.get(url)

        self.assertEqual(res.status_code, 500)
        self.assertEqual(res.data, {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."})
