from django.db import models
from django.db.models import IntegerChoices

from apps.core.models import TimeStampedModel


class CrawledLectureReview(TimeStampedModel):
    class RatingEnum(IntegerChoices):
        FIVE = 5, "5점"
        FOUR = 4, "4점"
        THREE = 3, "3점"
        TWO = 2, "2점"
        ONE = 1, "1점"

    lecture = models.ForeignKey(
        "lectures.CrawledLecture",
        on_delete=models.CASCADE,
        related_name="reviews",
        help_text="리뷰가 달린 강의의 id",
    )
    external_id = models.BigIntegerField(help_text="크롤링 한 사이트에서 받은 리뷰의 pk")
    rating = models.SmallIntegerField(choices=RatingEnum.choices, help_text="리뷰의 평점")
    content = models.TextField(help_text="리뷰 내용")

    class Meta:
        db_table = "crawled_lecture_reviews"
        ordering = ["-created_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["lecture", "external_id"], name="unique_lecture_review")]

    def __str__(self) -> str:
        return f"[{self.lecture.id}][{self.lecture.title}] ({self.rating}) {self.content}"
