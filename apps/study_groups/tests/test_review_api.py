from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from apps.study_groups.models import GroupMember, Review, StudyGroup

User = get_user_model()


class StudyGroupReviewAPITest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        # 테스트 유저 계정 2개 생성
        self.user1 = User.objects.create_user(
            nickname="user1",
            email="user1@example.com",
            phone_number="01000000001",
        )
        self.user2 = User.objects.create_user(
            nickname="user2",
            email="user2@example.com",
            phone_number="01000000002",
        )

        # 스터디그룹 미등록자 계정 생성
        self.outsider = User.objects.create_user(
            nickname="outsider",
            email="outsider@example.com",
            phone_number="01000000003",
        )

        # 스터디 그룹 생성
        now = timezone.now()
        self.study_group = StudyGroup.objects.create(
            name="study-1",
            introduction="intro",
            max_headcount=5,
            start_at=now,
            end_at=now + timedelta(days=7),
            status=StudyGroup.StudyGroupStatusChoices.PENDING,
        )

        # 유저 스터디그룹 멤버 등록
        GroupMember.objects.create(study_group_id=self.study_group, user_id=self.user1, is_leader=True)
        GroupMember.objects.create(study_group_id=self.study_group, user_id=self.user2, is_leader=False)

    def _auth(self, user: Any) -> None:
        # 실제 토큰 인증 대신, 테스트에서는 강제 인증으로 정상 플로우만 검증
        self.client.force_authenticate(user=user)
        self.client.force_login(user=user)

    def test_create_review_success_200_and_review_created(self) -> None:
        self._auth(self.user1)

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})
        payload = {"star_rating": 5, "content": "서로에게 너무나 유익한 스터디였습니다."}

        res = self.client.post(url, data=payload, format="json")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, {"detail": "스터디 리뷰 작성에 성공했습니다."})

        self.assertTrue(
            Review.objects.filter(
                user=self.user1,
                study_group=self.study_group,
                star_rating=5,
                content="서로에게 너무나 유익한 스터디였습니다.",
            ).exists()
        )

    def test_list_reviews_success_200_and_returns_array(self) -> None:
        self._auth(self.user1)

        # 리뷰 2개 생성 (내 리뷰, 다른 사람 리뷰)
        my_review = Review.objects.create(
            user=self.user1,
            study_group=self.study_group,
            star_rating=5,
            content="좋았어요",
        )
        other_review = Review.objects.create(
            user=self.user2,
            study_group=self.study_group,
            star_rating=3,
            content="그저 그랬어요",
        )

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.data, list)
        self.assertEqual(len(res.data), 2)

        # 응답 필드 검증
        for item in res.data:
            self.assertIn("id", item)
            self.assertIn("star_rating", item)
            self.assertIn("content", item)
            self.assertIn("created_at", item)
            self.assertIn("updated_at", item)
            self.assertIn("is_mine", item)

        by_id = {item["id"]: item for item in res.data}
        self.assertTrue(by_id[my_review.id]["is_mine"])
        self.assertFalse(by_id[other_review.id]["is_mine"])

    def test_update_review_success_200_and_reflects_changes(self) -> None:
        self._auth(self.user1)

        review = Review.objects.create(
            user=self.user1,
            study_group=self.study_group,
            star_rating=5,
            content="처음엔 아주 좋았어요",
        )

        url = reverse(
            "study-group-review-update",
            kwargs={"group_id": self.study_group.id, "review_id": review.id},
        )
        payload = {"star_rating": 3, "content": "그저 그랬던 것 같아요."}

        res = self.client.patch(url, data=payload, format="json")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["id"], review.id)
        self.assertEqual(res.data["star_rating"], 3)
        self.assertEqual(res.data["content"], "그저 그랬던 것 같아요.")
        self.assertIn("created_at", res.data)
        self.assertIn("updated_at", res.data)

        review.refresh_from_db()
        self.assertEqual(review.star_rating, 3)
        self.assertEqual(review.content, "그저 그랬던 것 같아요.")

    # 에러 케이스 - Create API
    def test_create_review_unauthenticated_401(self) -> None:
        self.client.logout()

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})
        res = self.client.post(url, data={"star_rating": 5, "content": "hi"}, format="json")

        self.assertEqual(res.status_code, 401)
        self.assertIn("error_detail", res.data)

    def test_create_review_group_not_found_404(self) -> None:
        self._auth(self.user1)

        url = reverse("study-group-review", kwargs={"group_id": 999999})
        res = self.client.post(url, data={"star_rating": 5, "content": "hi"}, format="json")

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, {"error_detail": "스터디 그룹을 찾을 수 없습니다."})

    def test_create_review_not_member_403(self) -> None:
        self._auth(self.outsider)

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})
        res = self.client.post(url, data={"star_rating": 5, "content": "hi"}, format="json")

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "소속된 스터디 그룹이 아닙니다."})

    def test_create_review_validation_error_missing_fields_400(self) -> None:
        self._auth(self.user1)

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})

        # star_rating 누락
        res = self.client.post(url, data={"content": "hi"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("error_detail", res.data)
        self.assertIn("star_rating", res.data["error_detail"])

    def test_create_review_validation_error_star_rating_out_of_range_400(self) -> None:
        self._auth(self.user1)

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})
        res = self.client.post(url, data={"star_rating": 6, "content": "hi"}, format="json")

        self.assertEqual(res.status_code, 400)
        self.assertIn("error_detail", res.data)
        self.assertIn("star_rating", res.data["error_detail"])

    def test_create_review_duplicate_review_integrity_error_400(self) -> None:
        self._auth(self.user1)

        Review.objects.create(user=self.user1, study_group=self.study_group, star_rating=5, content="이미 작성")

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})
        res = self.client.post(url, data={"star_rating": 4, "content": "또 작성"}, format="json")

        self.assertEqual(res.status_code, 400)
        self.assertEqual(
            res.data,
            {"error_detail": {"non_field_errors": ["이미 이 스터디 그룹에 대한 리뷰를 작성했습니다."]}},
        )

    def test_create_review_internal_error_500(self) -> None:
        self._auth(self.user1)

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})

        # serializer.save() 단계에서 예외 발생을 강제로 유도
        with patch("apps.study_groups.views.review_view.ReviewCreateSerializer.save", side_effect=Exception("boom")):
            res = self.client.post(url, data={"star_rating": 5, "content": "hi"}, format="json")

        self.assertEqual(res.status_code, 500)
        self.assertEqual(res.data, {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."})

    # 에러 케이스 - List API

    def test_list_reviews_unauthenticated_401(self) -> None:
        self.client.logout()

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."})

    def test_list_reviews_group_not_found_404(self) -> None:
        self._auth(self.user1)

        url = reverse("study-group-review", kwargs={"group_id": 999999})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, {"error_detail": "스터디 그룹을 찾을 수 없습니다."})

    def test_list_reviews_not_member_403(self) -> None:
        self._auth(self.outsider)

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "소속된 스터디 그룹이 아닙니다."})

    def test_list_reviews_success_returns_sorted_by_created_at_desc(self) -> None:
        self._auth(self.user1)

        r1 = Review.objects.create(user=self.user1, study_group=self.study_group, star_rating=5, content="old")
        r2 = Review.objects.create(user=self.user2, study_group=self.study_group, star_rating=4, content="new")

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)
        # created_at desc 정렬이면 최신(r2)이 앞에 와야 함
        self.assertEqual(res.data[0]["id"], r2.id)
        self.assertEqual(res.data[1]["id"], r1.id)

    def test_list_reviews_internal_error_500(self) -> None:
        self._auth(self.user1)

        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})

        with patch("apps.study_groups.views.review_view.Review.objects.filter", side_effect=Exception("boom")):
            res = self.client.get(url)

        self.assertEqual(res.status_code, 500)
        self.assertEqual(res.data, {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."})

    # 에러 케이스 - Update API

    def test_update_review_unauthenticated_401(self) -> None:
        self.client.logout()

        review = Review.objects.create(user=self.user1, study_group=self.study_group, star_rating=5, content="x")
        url = reverse(
            "study-group-review-update",
            kwargs={"group_id": self.study_group.id, "review_id": review.id},
        )
        res = self.client.patch(url, data={"star_rating": 3, "content": "y"}, format="json")

        self.assertEqual(res.status_code, 401)
        self.assertIn("error_detail", res.data)

    def test_update_review_group_not_found_404(self) -> None:
        self._auth(self.user1)

        review = Review.objects.create(user=self.user1, study_group=self.study_group, star_rating=5, content="x")
        url = reverse(
            "study-group-review-update",
            kwargs={"group_id": 999999, "review_id": review.id},
        )
        res = self.client.patch(url, data={"star_rating": 3, "content": "y"}, format="json")

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, {"error_detail": "스터디 그룹을 찾을 수 없습니다."})

    def test_update_review_not_member_403(self) -> None:
        self._auth(self.outsider)

        review = Review.objects.create(user=self.user1, study_group=self.study_group, star_rating=5, content="x")
        url = reverse(
            "study-group-review-update",
            kwargs={"group_id": self.study_group.id, "review_id": review.id},
        )
        res = self.client.patch(url, data={"star_rating": 3, "content": "y"}, format="json")

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "소속된 스터디 그룹이 아닙니다."})

    def test_update_review_not_found_404(self) -> None:
        self._auth(self.user1)

        url = reverse(
            "study-group-review-update",
            kwargs={"group_id": self.study_group.id, "review_id": 999999},
        )
        res = self.client.patch(url, data={"star_rating": 3, "content": "y"}, format="json")

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data, {"error_detail": "스터디 리뷰를 찾을 수 없습니다."})

    def test_update_review_forbidden_if_not_author_403(self) -> None:
        # user2가 작성한 리뷰를 user1이 수정 시도
        self._auth(self.user1)

        review = Review.objects.create(
            user=self.user2,
            study_group=self.study_group,
            star_rating=5,
            content="user2 review",
        )

        url = reverse(
            "study-group-review-update",
            kwargs={"group_id": self.study_group.id, "review_id": review.id},
        )
        res = self.client.patch(url, data={"star_rating": 3, "content": "hacked"}, format="json")

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "권한이 없습니다."})

    def test_update_review_validation_error_400(self) -> None:
        self._auth(self.user1)

        review = Review.objects.create(
            user=self.user1,
            study_group=self.study_group,
            star_rating=5,
            content="ok",
        )

        url = reverse(
            "study-group-review-update",
            kwargs={"group_id": self.study_group.id, "review_id": review.id},
        )

        # star_rating 범위 밖
        res = self.client.patch(url, data={"star_rating": 0, "content": "bad"}, format="json")

        self.assertEqual(res.status_code, 400)
        self.assertIn("error_detail", res.data)
        self.assertIn("star_rating", res.data["error_detail"])

    def test_update_review_internal_error_500(self) -> None:
        self._auth(self.user1)

        review = Review.objects.create(
            user=self.user1,
            study_group=self.study_group,
            star_rating=5,
            content="ok",
        )

        url = reverse(
            "study-group-review-update",
            kwargs={"group_id": self.study_group.id, "review_id": review.id},
        )

        with patch("apps.study_groups.views.review_view.ReviewUpdateSerializer.save", side_effect=Exception("boom")):
            res = self.client.patch(url, data={"star_rating": 3, "content": "y"}, format="json")

        self.assertEqual(res.status_code, 500)
        self.assertEqual(res.data, {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."})
