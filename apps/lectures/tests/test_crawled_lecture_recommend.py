from datetime import date
from unittest.mock import MagicMock, patch

import numpy as np
from django.test import TestCase

from apps.lectures.models import Category, CrawledLecture
from apps.lectures.services.recommendation.content_based import (
    build_user_vector,
    recommend_lectures,
)
from apps.study_groups.models import GroupMember, StudyGroup, StudyLecture
from apps.users.models import User


class RecommendLecturesTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(
            email="test@example.com",
            name="테스트유저",
            nickname="tester",
            phone_number="01012345678",
            gender="M",
            birthday=date(2000, 1, 1),
            profile_img_url="https://example.com/profile.png",
            is_active=True,
        )

        self.cat_python = Category.objects.create(name="Python")
        self.cat_network = Category.objects.create(name="Network")
        self.cat_algo = Category.objects.create(name="Algorithm")

        self.lec1 = CrawledLecture.objects.create(
            external_id=1,
            title="파이썬 기초",
            instructor="강사1",
            average_rating=4.5,
            total_class_time=10,
            difficulty=CrawledLecture.DifficultyEnum.EASY,
            description="desc",
            platform=CrawledLecture.PlatformEnum.INFLEARN,
            original_price=10000,
            discount_price=5000,
            url_link="https://example.com/1",
            thumbnail_img_url="https://example.com/1.png",
        )
        self.lec1.categories.add(self.cat_python)

        self.lec2 = CrawledLecture.objects.create(
            external_id=2,
            title="장고 심화",
            instructor="강사2",
            average_rating=4.6,
            total_class_time=12,
            difficulty=CrawledLecture.DifficultyEnum.NORMAL,
            description="desc",
            platform=CrawledLecture.PlatformEnum.INFLEARN,
            original_price=12000,
            discount_price=6000,
            url_link="https://example.com/2",
            thumbnail_img_url="https://example.com/2.png",
        )
        self.lec2.categories.add(self.cat_python)

        self.lec3 = CrawledLecture.objects.create(
            external_id=3,
            title="알고리즘",
            instructor="강사3",
            average_rating=4.7,
            total_class_time=15,
            difficulty=CrawledLecture.DifficultyEnum.HARD,
            description="desc",
            platform=CrawledLecture.PlatformEnum.UDEMY,
            original_price=15000,
            discount_price=7000,
            url_link="https://example.com/3",
            thumbnail_img_url="https://example.com/3.png",
        )
        self.lec3.categories.add(self.cat_algo)

        self.lec4 = CrawledLecture.objects.create(
            external_id=4,
            title="자료구조",
            instructor="강사4",
            average_rating=4.4,
            total_class_time=11,
            difficulty=CrawledLecture.DifficultyEnum.NORMAL,
            description="desc",
            platform=CrawledLecture.PlatformEnum.INFLEARN,
            original_price=11000,
            discount_price=5500,
            url_link="https://example.com/4",
            thumbnail_img_url="https://example.com/4.png",
        )
        self.lec4.categories.add(self.cat_algo)

        self.lec5 = CrawledLecture.objects.create(
            external_id=5,
            title="네트워크 기초",
            instructor="강사5",
            average_rating=4.3,
            total_class_time=9,
            difficulty=CrawledLecture.DifficultyEnum.EASY,
            description="desc",
            platform=CrawledLecture.PlatformEnum.UDEMY,
            original_price=9000,
            discount_price=4500,
            url_link="https://example.com/5",
            thumbnail_img_url="https://example.com/5.png",
        )
        self.lec5.categories.add(self.cat_network)

        self.group = StudyGroup.objects.create(
            name="test-group",
            introduction="intro",
            max_headcount=5,
            start_at="2024-01-01T00:00:00Z",
            end_at="2024-12-31T00:00:00Z",
        )

        GroupMember.objects.create(
            study_group_id=self.group,
            user_id=self.user,
        )

        StudyLecture.objects.create(
            lecture=self.lec3,
            study_group=self.group,
        )

    @patch("apps.lectures.services.recommendation.content_based.get_user_embedding_vector")
    @patch("apps.lectures.services.recommendation.content_based.get_lecture_embedding_vector")
    def test_personalized_recommendation_excludes_enrolled(
        self,
        mock_lec_vec: MagicMock,
        mock_user_vec: MagicMock,
    ) -> None:
        mock_lec_vec.side_effect = [
            np.array([0, 0, 1], dtype=np.float32),
            np.array([0, 1, 0], dtype=np.float32),
            np.array([0.95, 0, 0], dtype=np.float32),
            np.array([0.9, 0, 0], dtype=np.float32),
            np.array([1, 0, 0], dtype=np.float32),
        ]

        mock_user_vec.return_value = np.array([0.95, 0, 0], dtype=np.float32)

        recommended, rec_type = recommend_lectures(self.user, top_n=2)

        self.assertEqual(rec_type, "personalized")
        self.assertEqual(len(recommended), 2)

        self.assertNotIn(self.lec3, recommended)

        self.assertEqual(recommended[0], self.lec1)
        self.assertEqual(recommended[1], self.lec2)

    @patch("apps.lectures.services.recommendation.content_based.get_user_embedding_vector")
    def test_random_when_user_vector_missing(
        self,
        mock_user_vec: MagicMock,
    ) -> None:
        mock_user_vec.return_value = None

        recommended, rec_type = recommend_lectures(self.user, top_n=2)

        self.assertEqual(rec_type, "random")
        self.assertEqual(len(recommended), 2)

    @patch("apps.lectures.services.recommendation.content_based.get_user_embedding_vector")
    def test_random_when_all_lectures_enrolled(
        self,
        mock_user_vec: MagicMock,
    ) -> None:
        mock_user_vec.return_value = np.array([1, 0, 0], dtype=np.float32)

        for lec in [self.lec1, self.lec2, self.lec4, self.lec5]:
            StudyLecture.objects.create(lecture=lec, study_group=self.group)

        recommended, rec_type = recommend_lectures(self.user, top_n=2)

        self.assertEqual(rec_type, "random")

    def test_build_user_vector_with_weighted_average(self) -> None:
        self.user.lecture_bookmarks_middle_table.add(self.lec1)
        self.user.prefer_categories_middle_table.add(self.cat_network)

        v1 = np.array([1, 0, 0], dtype=np.float32)
        v3 = np.array([0, 1, 0], dtype=np.float32)
        v5 = np.array([0, 0, 1], dtype=np.float32)

        lecture_ids = [self.lec1.id, self.lec2.id, self.lec3.id, self.lec4.id, self.lec5.id]
        lecture_vectors = np.vstack(
            [v1, np.array([0, 0, 0], dtype=np.float32), v3, np.array([0, 0, 0], dtype=np.float32), v5]
        )

        expected_raw_vec = np.array([5 / 9, 3 / 9, 1 / 9], dtype=np.float32)

        norm = np.linalg.norm(expected_raw_vec)
        expected_user_vec = expected_raw_vec / norm

        user_vec = build_user_vector(self.user, lecture_vectors, lecture_ids)

        self.assertIsNotNone(user_vec)
        assert user_vec is not None
        self.assertEqual(user_vec.shape, (3,))

        np.testing.assert_allclose(user_vec, expected_user_vec, atol=1e-6)

    def test_build_user_vector_no_activities(self) -> None:
        StudyLecture.objects.all().delete()

        lecture_ids = [self.lec1.id]
        lecture_vectors = np.vstack(
            [
                np.array([1, 0, 0], dtype=np.float32),
            ]
        )

        user_vec = build_user_vector(self.user, lecture_vectors, lecture_ids)

        self.assertIsNone(user_vec)

    @patch("apps.lectures.services.recommendation.content_based.cache.get")
    @patch("apps.lectures.services.recommendation.content_based.cache.set")
    def test_get_lecture_embedding_vector_from_cache(
        self, mock_cache_set: MagicMock, mock_cache_get: MagicMock
    ) -> None:
        vec = np.zeros(384, dtype=np.float32)
        vec[:3] = [0.1, 0.2, 0.3]
        mock_cache_get.return_value = vec.tobytes()

        from apps.lectures.services.recommendation import content_based as cb

        result = cb.get_lecture_embedding_vector(self.lec1)
        assert result is not None
        np.testing.assert_allclose(result, vec)
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_not_called()

    @patch("apps.lectures.services.recommendation.content_based.cache.get")
    @patch("apps.lectures.services.recommendation.content_based.cache.set")
    def test_get_user_embedding_vector_from_cache(self, mock_cache_set: MagicMock, mock_cache_get: MagicMock) -> None:
        vec = np.zeros(384, dtype=np.float32)
        vec[:3] = [0.5, 0.6, 0.7]
        mock_cache_get.return_value = vec.tobytes()

        from apps.lectures.services.recommendation import content_based as cb

        result = cb.get_user_embedding_vector(self.user, np.vstack([vec]), [self.lec1.id])
        assert result is not None
        np.testing.assert_allclose(result, vec)
        mock_cache_get.assert_called_once()
        mock_cache_set.assert_not_called()

    @patch("apps.lectures.services.recommendation.content_based.cache.get")
    @patch("apps.lectures.services.recommendation.content_based.cache.set")
    @patch("apps.lectures.services.recommendation.content_based.build_lecture_embedding_vector")
    def test_get_lecture_embedding_vector_cache_miss(
        self, mock_build_vec: MagicMock, mock_cache_set: MagicMock, mock_cache_get: MagicMock
    ) -> None:
        mock_cache_get.return_value = None
        vec = np.zeros(384, dtype=np.float32)
        vec[:3] = [0.1, 0.2, 0.3]
        mock_build_vec.return_value = vec

        from apps.lectures.services.recommendation import content_based as cb

        result = cb.get_lecture_embedding_vector(self.lec1)
        assert result is not None
        np.testing.assert_allclose(result, vec)
        mock_cache_set.assert_called_once()

    @patch("apps.lectures.services.recommendation.content_based.cache.get")
    @patch("apps.lectures.services.recommendation.content_based.cache.set")
    @patch("apps.lectures.services.recommendation.content_based.build_user_vector")
    def test_get_user_embedding_vector_cache_miss(
        self, mock_build_user_vec: MagicMock, mock_cache_set: MagicMock, mock_cache_get: MagicMock
    ) -> None:
        mock_cache_get.return_value = None
        user_vec = np.zeros(384, dtype=np.float32)
        user_vec[:3] = [0.5, 0.6, 0.7]
        mock_build_user_vec.return_value = user_vec

        from apps.lectures.services.recommendation import content_based as cb

        result = cb.get_user_embedding_vector(self.user, np.vstack([user_vec]), [self.lec1.id])
        assert result is not None
        np.testing.assert_allclose(result, user_vec)
        mock_cache_set.assert_called_once()
