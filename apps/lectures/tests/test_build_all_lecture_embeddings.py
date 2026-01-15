import random

from django.core.cache import cache
from django.test import TestCase

from apps.lectures.models import Category, CrawledLecture
from apps.lectures.services.recommendation.content_based import (
    build_lecture_embed_cache_key,
)
from apps.lectures.tasks.embedding import build_all_lecture_embeddings


class BuildEmbeddingTaskTest(TestCase):
    def setUp(self) -> None:
        self.category = Category.objects.create(name="Python")

        self.lecture = CrawledLecture.objects.create(
            external_id=1,
            title="테스트 강의",
            instructor="강사 테스트",
            average_rating=4.5,
            total_class_time=12,
            difficulty=random.choice(
                [
                    CrawledLecture.DifficultyEnum.EASY,
                    CrawledLecture.DifficultyEnum.NORMAL,
                    CrawledLecture.DifficultyEnum.HARD,
                ]
            ),
            description="임베딩 대상",
            platform=random.choice([CrawledLecture.PlatformEnum.INFLEARN, CrawledLecture.PlatformEnum.UDEMY]),
            original_price=15000,
            discount_price=7000,
            url_link="https://example.com/1",
            thumbnail_img_url="https://example.com/1.png",
        )
        self.lecture.categories.add(self.category)

    def test_embedding_is_cached(self) -> None:
        count = build_all_lecture_embeddings.run()

        self.assertEqual(count, 1)

        key = build_lecture_embed_cache_key(self.lecture.id)
        cached_bytes = cache.get(key)
        self.assertIsNotNone(cached_bytes)
