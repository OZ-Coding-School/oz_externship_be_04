from __future__ import annotations

from datetime import timedelta
from typing import Any

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
            username="user1",
            email="user1@example.com",
            password="pw1234!",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="pw1234!",
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

        # 리뷰 2개 생성 (user1, user2)
        Review.objects.create(user=self.user1, study_group=self.study_group, star_rating=5, content="좋았어요")
        Review.objects.create(user=self.user2, study_group=self.study_group, star_rating=3, content="그저 그랬어요")

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
