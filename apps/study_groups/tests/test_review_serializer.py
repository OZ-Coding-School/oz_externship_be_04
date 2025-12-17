from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.study_groups.models import Review, StudyGroup
from apps.study_groups.serializers.review_serializer import (
    ReviewCreateSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
)

User = get_user_model()


class ReviewSerializerUnitTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            nickname="ser_user",
            email="ser_user@example.com",
            phone_number="01099990001",
        )

        now = timezone.now()
        self.study_group = StudyGroup.objects.create(
            name="ser-study-1",
            introduction="intro",
            max_headcount=5,
            start_at=now,
            end_at=now + timedelta(days=7),
            status=StudyGroup.StudyGroupStatusChoices.PENDING,
        )

    def test_review_create_serializer_validate_star_rating_success(self) -> None:
        s = ReviewCreateSerializer(data={"star_rating": 5, "content": "ok"}, context={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_review_create_serializer_validate_star_rating_fail(self) -> None:
        s = ReviewCreateSerializer(data={"star_rating": 6, "content": "bad"}, context={})
        self.assertFalse(s.is_valid())
        self.assertIn("star_rating", s.errors)

    def test_review_create_serializer_create_already_created_review(self) -> None:
        # create() 내부에서 context["request"].user / context["study_group"] 를 사용
        dummy_request = SimpleNamespace(user=self.user)

        s = ReviewCreateSerializer(
            data={"star_rating": 4, "content": "created"},
            context={"request": dummy_request, "study_group": self.study_group},
        )
        self.assertTrue(s.is_valid(), s.errors)

        review = s.save()
        self.assertIsInstance(review, Review)
        self.assertEqual(review.user_id, self.user.id)
        self.assertEqual(review.study_group_id, self.study_group.id)
        self.assertEqual(review.star_rating, 4)
        self.assertEqual(review.content, "created")

    def test_review_update_serializer_validate_star_rating_fail(self) -> None:
        review = Review.objects.create(user=self.user, study_group=self.study_group, star_rating=3, content="before")
        s = ReviewUpdateSerializer(instance=review, data={"star_rating": 0, "content": "after"})
        self.assertFalse(s.is_valid())
        self.assertIn("star_rating", s.errors)

    def test_review_update_serializer_update_updates_instance(self) -> None:
        review = Review.objects.create(user=self.user, study_group=self.study_group, star_rating=3, content="before")
        s = ReviewUpdateSerializer(instance=review, data={"star_rating": 5, "content": "after"})
        self.assertTrue(s.is_valid(), s.errors)

        updated = s.save()
        self.assertEqual(updated.id, review.id)
        self.assertEqual(updated.star_rating, 5)
        self.assertEqual(updated.content, "after")

        review.refresh_from_db()
        self.assertEqual(review.star_rating, 5)
        self.assertEqual(review.content, "after")

    def test_review_serializer_representation_fields(self) -> None:
        review = Review.objects.create(user=self.user, study_group=self.study_group, star_rating=5, content="hello")
        data = ReviewSerializer(review).data
        self.assertIn("id", data)
        self.assertEqual(data["star_rating"], 5)
        self.assertEqual(data["content"], "hello")
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)
