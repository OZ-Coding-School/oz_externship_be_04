from typing import Any, Dict, List

from apps.chat.models import ChatMessage


class HistoryService:
    @staticmethod
    def get_recent_messages(group_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        msgs = (
            ChatMessage.objects.filter(study_group_id=group_id)
            .exclude(sender__isnull=True)
            .select_related("sender")
            .order_by("-id")[:limit]
        )

        return [
            {
                "id": m.id,
                "content": m.content,
                "sender": {
                    "id": m.sender_id,
                    "nickname": m.sender.nickname,
                },
                "created_at": m.created_at.isoformat(),
            }
            for m in reversed(msgs)
            if m.sender
        ]
