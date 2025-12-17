from typing import Optional

from apps.chat.models import ChatMessage, LastReadMessage


class ReadService:
    @staticmethod
    def update_last_read(
        *,
        user_id: int,
        group_id: int,
        message: ChatMessage,
    ) -> None:
        LastReadMessage.objects.update_or_create(
            user_id=user_id,
            study_group_id=group_id,
            defaults={"message": message},
        )

    @staticmethod
    def mark_all_read(
        *,
        user_id: int,
        group_id: int,
    ) -> None:
        last_msg: Optional[ChatMessage] = ChatMessage.objects.filter(study_group_id=group_id).order_by("-id").first()

        if last_msg:
            LastReadMessage.objects.update_or_create(
                user_id=user_id,
                study_group_id=group_id,
                defaults={"message": last_msg},
            )
