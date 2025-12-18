from __future__ import annotations

from datetime import timedelta
from typing import Any
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient, APITestCase

from apps.study_groups.models import GroupMember, Review, StudyGroup

User = get_user_model()


class ReviewViewBranchTest(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.user = User.objects.create_user(
            nickname="test_user",
            email="branch_user@example.com",
            phone_number="01099990002",
        )

        now = timezone.now()
        self.study_group = StudyGroup.objects.create(
            name="branch-study-1",
            introduction="intro",
            max_headcount=5,
            start_at=now,
            end_at=now + timedelta(days=7),
            status=StudyGroup.StudyGroupStatusChoices.PENDING,
        )

        GroupMember.objects.create(study_group_id=self.study_group, user_id=self.user, is_leader=True)

        self.client.force_authenticate(user=self.user)

    def test_create_api_permission_denied_branch_403(self) -> None:
        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})

        with patch(
            "apps.study_groups.views.review_view.StudyGroupReviewCreateAPIView.post",
            side_effect=PermissionDenied(),
        ):
            # post 자체를 PermissionDenied로 터뜨려 except PermissionDenied 라인을 커버
            res = self.client.post(url, data={"star_rating": 5, "content": "x"}, format="json")

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "권한이 없습니다."})

    def test_list_api_permission_denied_branch_403(self) -> None:
        url = reverse("study-group-review", kwargs={"group_id": self.study_group.id})

        with patch(
            "apps.study_groups.views.review_view.StudyGroupReviewCreateAPIView.get",
            side_effect=PermissionDenied(),
        ):
            res = self.client.get(url)

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "권한이 없습니다."})

    def test_update_api_permission_denied_branch_403(self) -> None:
        review = Review.objects.create(user=self.user, study_group=self.study_group, star_rating=5, content="x")
        url = reverse(
            "study-group-review-update",
            kwargs={"group_id": self.study_group.id, "review_id": review.id},
        )

        with patch(
            "apps.study_groups.views.review_view.StudyGroupReviewUpdateAPIView.patch",
            side_effect=PermissionDenied(),
        ):
            res = self.client.patch(url, data={"star_rating": 3, "content": "y"}, format="json")

        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data, {"error_detail": "권한이 없습니다."})
