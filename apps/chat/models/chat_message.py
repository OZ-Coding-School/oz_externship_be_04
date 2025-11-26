from django.db import models

from apps.core.models import TimeStampedModel


class ChatMessage(TimeStampedModel):
    # 메시지를 보낸 사용자 (탈퇴 시 기록 유지 위해 null)
    sender = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,  # 사용자 탈퇴 시 sender_id = null
        null=True,
        related_name="sent_messages",
    )
    # 해달 메시지가 속한 스터디 그룹
    study_group = models.ForeignKey(
        "study_groups.StudyGroup",
        on_delete=models.CASCADE,  # 스터디 그룹 삭제 시 메시지도 같이 삭제함
        related_name="chat_messages",
    )
    # 메시지 내용
    content = models.CharField(max_length=1000)

    class Meta:
        db_table = "chat_messages"
        indexes = [
            # 특정 스터디 그룹의 메시지를 시간순으로 빠르게 검색하기 위함
            models.Index(fields=["study_group", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.sender} @ {self.study_group}: {self.content[:20]}"
