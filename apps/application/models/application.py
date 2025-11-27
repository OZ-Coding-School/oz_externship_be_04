import uuid

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class ApplicationStatus(models.TextChoices):
    PENDING = "PENDING", "대기중"
    CANCELED = "CANCELED", "취소됨"
    ACCEPTED = "ACCEPTED", "승인됨"
    REJECTED = "REJECTED", "거절됨"


class Application(TimeStampedModel):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, help_text="보안을 위한 식별자")

    recruitment = models.ForeignKey(
        "recruitment.Recruitment", on_delete=models.CASCADE, related_name="applications", help_text="지원한 공고"
    )

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
        help_text="지원자가 지원한 공고",
    )

    objective = models.CharField(max_length=300, help_text="지원 목표")
    motivation = models.TextField(help_text="지원 동기")
    self_introduction = models.TextField(help_text="자기 소개")

    available_time = models.CharField(max_length=100, help_text="예시: 주 2회, 월/수 저녁 7시 이후 참여 가능")

    has_study_experience = models.BooleanField(default=False, help_text="과거에 스터디 참여한 경험이 있는지 여부")

    study_experience = models.TextField(blank=True, help_text="스터디 경험이 있다면 기재해주세요")

    status = models.CharField(
        choices=ApplicationStatus.choices,
        max_length=20,
        default=ApplicationStatus.PENDING,
        help_text="지원서 현재 진행 상태(대기, 취소 ,승인, 거절)",
    )

    class Meta:
        db_table = "applications"

        constraints = [
            models.UniqueConstraint(
                fields=["applicant", "recruitment"], name="unique_application_per_applicant_per_recruitment"
            )
        ]

        indexes = [
            models.Index(fields=["recruitment", "status", "-created_at"]),
            models.Index(fields=["applicant", "-created_at"]),
        ]

    def __str__(self) -> str:
        recruitment_title = self.recruitment.title if self.recruitment else "삭제된 공고"
        applicant_display = getattr(self.applicant, "nickname", "탈퇴한 유저")

        return f"[{recruitment_title}] {applicant_display} (UUID: {self.uuid})"