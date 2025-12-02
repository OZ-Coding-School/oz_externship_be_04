from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.db.models.enums import TextChoices

from apps.core.models import TimeStampedModel

if TYPE_CHECKING:
    from apps.lectures.models import Category, CrawledLectureReview


class CrawledLecture(TimeStampedModel):
    class DifficultyEnum(TextChoices):
        EASY = "EASY", "초급"
        NORMAL = "NORMAL", "중급"
        HARD = "HARD", "어려움"

    class PlatformEnum(TextChoices):
        INFLEARN = "INFLEARN", "인프런"
        UDEMY = "UDEMY", "유데미"

    external_id = models.BigIntegerField(help_text="크롤링 한 사이트에서 받은 강의의 pk")
    title = models.CharField(max_length=255, help_text="강의명")
    instructor = models.CharField(max_length=20, help_text="강사명")
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, help_text="리뷰 평점")
    total_class_time = models.SmallIntegerField(help_text="총 강의 시간")
    difficulty = models.CharField(max_length=20, choices=DifficultyEnum.choices, help_text="강의 난이도")
    description = models.TextField(help_text="간략한 강의 상세 설명")
    platform = models.CharField(max_length=20, choices=PlatformEnum.choices, help_text="플랫폼")
    original_price = models.BigIntegerField(null=True, default=0, help_text="강의 원가격")
    discount_price = models.BigIntegerField(null=True, default=0, help_text="강의 할인가격")
    url_link = models.URLField(max_length=255, help_text="강의 바로가기 링크")
    thumbnail_img_url = models.URLField(null=True, max_length=255, help_text="강의 썸네일 이미지")
    categories = models.ManyToManyField(
        "lectures.Category", through="lectures.LectureCategory", related_name="lectures"
    )

    class Meta:
        ordering = ["-created_at", "-id"]
        db_table = "crawled_lectures"
        constraints = [models.UniqueConstraint(fields=["platform", "external_id"], name="unique_platform_external_id")]

    def __str__(self) -> str:
        return f"[{self.difficulty}] ({self.instructor}) {self.title}"

    @property
    def mock_crawled_lecture_categories(self) -> list[Category]:
        import random
        from datetime import datetime, timedelta

        tags = [
            "artificial-intelligence",
            "Applied-ai",
            "it-programming",
            "game-dev-all",
            "data-science",
            "it",
            "hardware",
            "design",
        ]

        from apps.lectures.models import Category

        return [
            Category(
                id=random.randint(1, 100),
                name=tag,
                created_at=(now := datetime(random.randint(2000, 2025), random.randint(1, 12), random.randint(1, 28))),
                updated_at=now + timedelta(days=random.randint(0, 365)),
            )
            for tag in random.sample(tags, 2)
        ]

    @property
    def mock_crawled_lecture_reviews(self) -> list[CrawledLectureReview]:
        import random
        from datetime import datetime, timedelta

        from apps.lectures.models.crawled_lecture_review import CrawledLectureReview

        return [
            CrawledLectureReview(
                id=random.randint(1, 100),
                lecture=self,
                external_id=random.randint(1, 100),
                rating=random.choice([rating[0] for rating in CrawledLectureReview.RatingEnum.choices]),
                content=f"예시 내용{i}",
                created_at=(now := datetime(random.randint(2000, 2025), random.randint(1, 12), random.randint(1, 28))),
                updated_at=now + timedelta(days=random.randint(0, 365)),
            )
            for i in range(1, 5)
        ]
