import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.study_groups.models import StudyGroup


def get_default_close_at() -> datetime:
    return timezone.now() + timedelta(days=14)


class Recruitment(models.Model):
    """스터디 구인 공고"""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, help_text="외부 노출용 ID")
    study_group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name="recruitments",
        db_column="study_group_id",
        help_text="스터디 그룹",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruitments",
        db_column="author_id",
        help_text="공고 작성자",
    )
    title = models.CharField(max_length=50, help_text="공고 제목")
    content = models.TextField(help_text="공고 내용")
    estimated_fee = models.PositiveIntegerField(help_text="예상되는 강의 결제 비용")
    expected_headcount = models.SmallIntegerField(
        validators=[
            MinValueValidator(1, message="최소 1명 이상이어야 합니다."),
            MaxValueValidator(10, message="최대 10명까지 모집 가능합니다."),
        ],
        help_text="예상 모집 인원 (1~10명)",
    )
    views_count = models.PositiveIntegerField(default=0, help_text="조회수")
    close_at = models.DateTimeField(default=get_default_close_at, help_text="공고 마감일")
    is_closed = models.BooleanField(default=False, help_text="공고 마감 상태")
    created_at = models.DateTimeField(auto_now_add=True, help_text="공고 생성일")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, help_text="공고 수정일")

    class Meta:
        db_table = "recruitments"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["uuid"], name="idx_uuid"),
            models.Index(fields=["study_group"], name="idx_study_group"),
            models.Index(fields=["author"], name="idx_author"),
            models.Index(fields=["is_closed", "-created_at"], name="idx_closed_created"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(expected_headcount__gte=1, expected_headcount__lte=10),
                name="check_expected_headcount_range",
            )
        ]

    def __str__(self) -> str:
        return f"{self.title} - {self.study_group}"
