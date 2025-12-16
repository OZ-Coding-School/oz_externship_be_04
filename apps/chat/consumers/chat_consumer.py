import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from channels.db import database_sync_to_async  # type: ignore
from channels.generic.websocket import AsyncWebsocketConsumer  # type: ignore
from django_redis import get_redis_connection  # type: ignore
from rest_framework_simplejwt.tokens import AccessToken

from apps.chat.models import ChatMessage, LastReadMessage
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models import User


class ChatConsumer(AsyncWebsocketConsumer):  # type: ignore
    user: User
    group_id: int
    group_uuid: UUID
    room_group_name: str

    async def connect(self) -> None:
        try:
            raw_id = self.scope["url_route"]["kwargs"].get("group_id")
            self.group_id = int(raw_id)
        except Exception:
            await self.close(4000)
            return

        # 인증
        user = await self.authenticate()
        if user is None:
            await self.close(4001)
            return

        self.user = user

        # 멤버 검증
        is_member = await self.check_member()
        if not is_member:
            await self.close(4003)
            return

        try:
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        except Exception:
            await self.close(4500)
            return

        # 온라인 유저 등록
        try:
            redis = get_redis_connection("default")
            redis.sadd(f"chat_online:{self.group_id}", self.user.id)
        except Exception:
            pass

        # presence
        try:
            members = await self.get_group_members()
            await self.safe_send(
                {
                    "type": "presence",
                    "members": members,
                }
            )
        except Exception:
            pass

        # 입장 broadcast
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_join",
                "user": {"id": self.user.id, "nickname": self.user.nickname},
            },
        )

        # 메시지 히스토리
        history = await self.get_recent_messages(limit=100)
        await self.safe_send({"type": "history", "messages": history})

        # 읽음 처리
        await self.mark_all_read(self.user.id, self.group_id)

    async def disconnect(self, code: int) -> None:
        user: Optional[User] = getattr(self, "user", None)

        # 온라인 제거
        if user is not None:
            try:
                redis = get_redis_connection("default")
                redis.srem(f"chat_online:{self.group_id}", user.id)
            except Exception:
                pass

        # 그룹 제거
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception:
            pass

        # 퇴장 broadcast
        if user is not None:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_leave",
                    "user": {"id": user.id, "nickname": user.nickname},
                },
            )

    async def receive(self, text_data: str) -> None:
        try:
            data: Dict[str, Any] = json.loads(text_data)
        except Exception:
            return

        content = data.get("content")
        if not isinstance(content, str) or not content.strip():
            return

        user: Optional[User] = getattr(self, "user", None)
        if user is None:
            return

        msg = await self.save_message(content)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": msg.id,
                    "content": msg.content,
                    "sender": {"id": user.id, "nickname": user.nickname},
                    "created_at": msg.created_at.isoformat(),
                },
            },
        )

        await self.update_last_read(msg)

    async def chat_message(self, event: Dict[str, Any]) -> None:
        message = event.get("message")
        if not message:
            return
        await self.safe_send({"type": "message", **message})

    async def user_join(self, event: Dict[str, Any]) -> None:
        await self.safe_send({"type": "user_join", "user": event.get("user")})

    async def user_leave(self, event: Dict[str, Any]) -> None:
        await self.safe_send({"type": "user_leave", "user": event.get("user")})

    async def safe_send(self, payload: Dict[str, Any]) -> None:
        try:
            await self.send(text_data=json.dumps(payload))
        except Exception:
            pass

    @database_sync_to_async  # type: ignore[misc]
    def authenticate(self) -> Optional[User]:
        try:
            qs = self.scope["query_string"].decode()
            params = dict(x.split("=") for x in qs.split("&") if "=" in x)
            token = params.get("token")
            if not token:
                return None

            access = AccessToken(token)
            return User.objects.get(id=access["user_id"])
        except Exception:
            return None

    @database_sync_to_async  # type: ignore[misc]
    def check_member(self) -> bool:
        return GroupMember.objects.filter(study_group_id=self.group_id, user_id=self.user.id).exists()

    @database_sync_to_async  # type: ignore[misc]
    def get_group_members(self) -> List[Dict[str, Any]]:
        members = GroupMember.objects.filter(study_group_id=self.group_id).select_related("user")

        redis = get_redis_connection("default")
        online_set = redis.smembers(f"chat_online:{self.group_id}")
        online_ids = {int(uid) for uid in online_set}

        result = []
        for m in members:
            result.append(
                {
                    "id": m.user.id,  # type: ignore[attr-defined]
                    "nickname": m.user.nickname,  # type: ignore[attr-defined]
                    "is_online": m.user.id in online_ids,  # type: ignore[attr-defined]
                    "is_host": m.is_leader,
                }
            )

        return result

    @database_sync_to_async  # type: ignore[misc]
    def save_message(self, content: str) -> ChatMessage:
        group = StudyGroup.objects.get(id=self.group_id)
        return ChatMessage.objects.create(
            study_group=group,
            sender=self.user,
            content=content,
        )

    @database_sync_to_async  # type: ignore[misc]
    def update_last_read(self, msg: ChatMessage) -> None:
        LastReadMessage.objects.update_or_create(
            study_group_id=self.group_id,
            user_id=self.user.id,
            defaults={"message": msg},
        )

    @database_sync_to_async  # type: ignore[misc]
    def get_recent_messages(self, limit: int) -> List[Dict[str, Any]]:
        msgs = (
            ChatMessage.objects.filter(study_group_id=self.group_id)
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

    @database_sync_to_async  # type: ignore[misc]
    def mark_all_read(self, user_id: int, group_id: int) -> None:
        last_msg = ChatMessage.objects.filter(study_group_id=group_id).last()
        if last_msg:
            LastReadMessage.objects.update_or_create(
                user_id=user_id,
                study_group_id=group_id,
                defaults={"message": last_msg},
            )
