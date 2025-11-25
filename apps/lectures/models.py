import uuid

from django.db import models
from django.db.models.enums import TextChoices


class CrawledLectures(models.Model):
    class DifficultyEnum(TextChoices):
        EASY = "EASY", "초급"
        NORMAL = "NORMAL", "중급"
        HARD = "HARD", "어려움"

    class PlatformEnum(TextChoices):
        INFLEARN = "INFLEARN", "인프런"
        UDEMY = "UDEMY", "유데미"

    external_id = models.BigIntegerField(null=False, blank=False, help_text="크롤링 한 사이트에서 받은 강의의 pk")
    title = models.CharField(max_length=255, null=False, blank=False, help_text="강의명")
    instructor = models.CharField(max_length=20, null=False, blank=False, help_text="강사명")
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, null=False, blank=False, help_text="리뷰 평점")
    total_class_time = models.SmallIntegerField(null=False, blank=False, help_text="총 강의 시간")
    difficulty = models.CharField(
        max_length=20, null=False, blank=False, choices=DifficultyEnum.choices, help_text="강의 난이도"
    )
    description = models.TextField(null=False, blank=False, help_text="간략한 강의 상세 설명")
    platform = models.CharField(
        max_length=20, null=False, blank=False, choices=PlatformEnum.choices, help_text="플랫폼"
    )
    original_price = models.BigIntegerField(null=True, blank=True, default=0, help_text="강의 원가격")
    discount_price = models.BigIntegerField(null=True, blank=True, default=0, help_text="강의 할인가격")
    url_link = models.URLField(null=False, blank=False, max_length=255, help_text="강의 바로가기 링크")
    thumbnail_img_url = models.URLField(null=True, blank=True, max_length=255, help_text="강의 썸네일 이미지")
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [models.UniqueConstraint(fields=["platform", "external_id"], name="unique_platform_external_id")]

    def __str__(self) -> str:
        return f"[{self.difficulty}★] ({self.instructor}) {self.title} "
