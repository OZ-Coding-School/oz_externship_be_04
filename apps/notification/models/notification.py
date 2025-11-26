from django.db import models

from apps.core.models import BaseModel


class Notification(BaseModel):
    class NotificationType(models.TextChoices):
        STUDY_JOIN = "STUDY_JOIN", "스터디 그룹에 새로운 구성원이 참가한 경우 알림"
        STUDY_NOTE_CREATE = "STUDY_NOTE_CREATE", "스터디 구성원이 스터디 기록을 작성한 경우 알림"
        STUDY_REVIEW_REQUEST = "STUDY_REVIEW_REQUEST", "스터디 종료가 도래한 경우 알림"
        APPLICATION_ACCEPT = "APPLICATION_ACCEPT", "지원내역이 승인된 경우 알림"
        APPLICATION_REJECT = "APPLICATION_REJECT", "지원내역이 거절된 경우 알림"
        ADD_APPLICATION = "ADD_APPLICATION", "공고를 올린 스터디 그룹의 리더에게 새로운 지원내역이 있는 경우 알림"
        TODAY_SCHEDULE = "TODAY_SCHEDULE", "금일 스케줄 알림"
        UPCOMING_SCHEDULE = "UPCOMING_SCHEDULE", "스케줄 하루 전에 임박한 예정 스케줄 알림"

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, null=False, related_name="notifications")
    content = models.CharField(max_length=300)
    type = models.CharField(choices=NotificationType.choices)
    is_read = models.BooleanField(default=False)
    back_url_link = models.CharField(max_length=500)

    class Meta:
        db_table = "notification"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} : {self.user}"
