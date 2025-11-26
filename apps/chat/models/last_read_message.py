from django.db import models
from apps.core.models import TimeStampedModel


class LastReadMessage(TimeStampedModel):
    study_group = models.ForeignKey(
        "study_groups.StudyGroup",
        on_delete=models.CASCADE,  # 스터디 그룹 삭제시 해당 그룹의 읽음 상태가 의미 없음
        related_name="last_read_messages",
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,  # 유저가 그룹 나가기, 탈퇴시 유저의 읽음 기록은 필요 없음
        related_name="last_read_messages",
    )
    message = models.ForeignKey(
        "chat.ChatMessage",
        on_delete=models.CASCADE,  # 해당 메시지 삭제시 마지막으로 읽었다고 기록된 last_read도 삭제
        related_name="last_read_by_users",
    )

    class Meta:
        db_table = "last_read_messages" # 복수형으로 변경했습니다
        constraints = [
            # 유저는 각 그룹마다 last_read 메시지가 하나만 존재해야 함
            models.UniqueConstraint(fields=["study_group", "user"], name="unique_user_group_last_read")
        ]

    def __str__(self):
        return f"{self.user} - {self.study_group} / last: {self.message}"