import json
from typing import Any, Dict, List, Optional

# [수정] channels 관련 import에 type: ignore 추가
from channels.db import database_sync_to_async  # type: ignore
from channels.generic.websocket import AsyncWebsocketConsumer  # type: ignore
from rest_framework_simplejwt.tokens import AccessToken

from apps.chat.models import ChatMessage
from apps.chat.services.history_service import HistoryService
from apps.chat.services.message_service import MessageService
from apps.chat.services.presence_service import PresenceService
from apps.chat.services.read_service import ReadService
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models import User


class ChatConsumer(AsyncWebsocketConsumer):  # type: ignore
    user: User
    group_id: int
    room_group_name: str

    async def connect(self) -> None:
        try:
            raw_id = self.scope["url_route"]["kwargs"].get("group_id")
            self.group_id = int(raw_id)
            self.room_group_name = f"chat_{self.group_id}"
        except Exception:
            await self.close(4000)
            return

        # asgi.py JWTAuthMiddlewareStack에서 파싱
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(4001)
            return

        self.user = user

        # 멤버 검증
        is_member = await self.check_member()
        if not is_member:
            await self.close(4003)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        try:
            await database_sync_to_async(PresenceService.add)(self.group_id, self.user.id)
        except Exception:
            pass

        members = await self.get_presence()
        await self.safe_send(
            {
                "type": "presence",
                "members": members,
            }
        )

        # user_join broadcast
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_join",
                "user": {
                    "id": self.user.id,
                    "nickname": self.user.nickname,
                },
            },
        )

        # history
        history = await self.get_history(limit=100)
        await self.safe_send(
            {
                "type": "history",
                "messages": history,
            }
        )

        # 읽음 처리
        await self.mark_all_read_service()

    async def disconnect(self, code: int) -> None:
        user: Optional[User] = getattr(self, "user", None)

        if user:
            try:
                await database_sync_to_async(PresenceService.remove)(self.group_id, user.id)
            except Exception:
                pass

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_leave",
                    "user": {
                        "id": user.id,
                        "nickname": user.nickname,
                    },
                },
            )

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name,
        )

    async def receive(self, text_data: str) -> None:
        try:
            data = json.loads(text_data)
        except Exception:
            return

        content = data.get("content")
        if not isinstance(content, str) or not content.strip():
            return

        msg = await self.create_message(content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": msg.id,
                    "content": msg.content,
                    "sender": {
                        "id": self.user.id,
                        "nickname": self.user.nickname,
                    },
                    "created_at": msg.created_at.isoformat(),
                },
            },
        )

        await self.update_last_read_service(msg)

    async def chat_message(self, event: Dict[str, Any]) -> None:
        await self.safe_send({"type": "message", **event["message"]})

    async def user_join(self, event: Dict[str, Any]) -> None:
        await self.safe_send({"type": "user_join", "user": event["user"]})

    async def user_leave(self, event: Dict[str, Any]) -> None:
        await self.safe_send({"type": "user_leave", "user": event["user"]})

    async def safe_send(self, payload: Dict[str, Any]) -> None:
        try:
            await self.send(text_data=json.dumps(payload, ensure_ascii=False))
        except Exception:
            pass

    @database_sync_to_async  # type: ignore
    def check_member(self) -> bool:
        return GroupMember.objects.filter(
            study_group_id=self.group_id,
            user_id=self.user.id,
        ).exists()

    @database_sync_to_async  # type: ignore
    def get_presence(self) -> list[dict[str, Any]]:
        return PresenceService.get_members(self.group_id)

    @database_sync_to_async  # type: ignore
    def create_message(self, content: str) -> ChatMessage:
        group = StudyGroup.objects.get(id=self.group_id)
        return MessageService.create_message(
            study_group=group,
            user=self.user,
            content=content,
        )

    @database_sync_to_async  # type: ignore
    def get_history(self, limit: int) -> list[dict[str, Any]]:
        return HistoryService.get_recent_messages(
            group_id=self.group_id,
            limit=limit,
        )

    @database_sync_to_async  # type: ignore
    def update_last_read_service(self, msg: ChatMessage) -> None:
        ReadService.update_last_read(
            user_id=self.user.id,
            group_id=self.group_id,
            message=msg,
        )

    @database_sync_to_async  # type: ignore
    def mark_all_read_service(self) -> None:
        ReadService.mark_all_read(
            user_id=self.user.id,
            group_id=self.group_id,
        )
