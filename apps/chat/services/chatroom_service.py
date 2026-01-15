from typing import Any, Dict, List, Optional

from django.db.models import Count, QuerySet
from rest_framework.exceptions import PermissionDenied

from apps.chat.models.chat_message import ChatMessage
from apps.chat.models.last_read_message import LastReadMessage
from apps.chat.services.last_read_service import LastReadService
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models import User


class ChatRoomService:
    # 스터디 그룹의 채팅 조회 기능 담당

    @staticmethod
    def validate_member(study_group: StudyGroup, user: User) -> None:
        """
        요청한 사용자가 해당 그룹 구성원인지 검사.
        구성원이 아니라면 PermissionDenied 예외 발생.
        """
        exists = GroupMember.objects.filter(
            study_group_id=study_group.id,
            user_id=user.id,
        ).exists()

        if not exists:
            raise PermissionDenied("그룹 멤버만 채팅을 조회할 수 있습니다.")

    @staticmethod
    def get_chatrooms(user: User) -> List[Dict[str, Any]]:
        memberships = GroupMember.objects.filter(user_id=user.id).select_related("study_group_id")
        groups = [m.study_group_id for m in memberships]
        group_ids = [g.id for g in groups]

        if not group_ids:
            return []

        last_messages = (
            ChatMessage.objects.filter(study_group_id__in=group_ids)
            .select_related("sender", "study_group")
            .order_by("study_group_id", "-created_at")
        )

        last_message_map: Dict[int, ChatMessage] = {}
        for msg in last_messages:
            if msg.study_group_id not in last_message_map:
                last_message_map[msg.study_group_id] = msg

        last_reads = LastReadMessage.objects.filter(user_id=user.id, study_group_id__in=group_ids).select_related(
            "message"
        )
        last_read_map = {lr.study_group_id: lr for lr in last_reads}

        count_map = dict(
            ChatMessage.objects.filter(study_group_id__in=group_ids)
            .values_list("study_group_id")
            .annotate(total=Count("id"))
        )

        results: List[Dict[str, Any]] = []

        for group in groups:
            last_message = last_message_map.get(group.id)
            last_read = last_read_map.get(group.id)

            if last_read:
                unread_count = ChatMessage.objects.filter(
                    study_group_id=group.id,
                    created_at__gt=last_read.message.created_at,
                ).count()
            else:
                unread_count = count_map.get(group.id, 0)

            if last_message:
                sender = last_message.sender
                assert sender is not None

                last_message_data = {
                    "id": last_message.id,
                    "sender": {
                        "id": sender.id,
                        "nickname": sender.nickname,
                    },
                    "content": last_message.content,
                    "created_at": last_message.created_at,
                    "is_read": bool(last_read),
                }
            else:
                last_message_data = None

            results.append(
                {
                    "group_id": group.id,
                    "group_name": group.name,
                    "unread_count": unread_count,
                    "last_message": last_message_data,
                }
            )

        return results

    @staticmethod
    def get_room_info(study_group: StudyGroup, user: User) -> Dict[str, Any]:
        ChatRoomService.validate_member(study_group, user)

        members = GroupMember.objects.filter(study_group_id=study_group.id).select_related("user_id")

        member_list = [{"nickname": m.user_id.nickname, "is_leader": m.is_leader} for m in members]

        return {
            "group_id": study_group.id,
            "group_name": study_group.name,
            "members": member_list,
        }

    @staticmethod
    def get_messages(
        study_group: StudyGroup,
        user: User,
        cursor: Optional[int] = None,
        limit: int = 300,
    ) -> QuerySet[ChatMessage]:

        ChatRoomService.validate_member(study_group, user)

        membership = GroupMember.objects.get(
            study_group_id=study_group.id,
            user_id=user.id,
        )

        qs = (
            ChatMessage.objects.filter(
                study_group_id=study_group.id,
                created_at__gte=membership.created_at,
            )
            .select_related("sender")
            .order_by("-id")
        )

        if cursor:
            qs = qs.filter(id__lte=cursor)

        return qs

    @staticmethod
    def mark_all_read(study_group: StudyGroup, user: User) -> None:
        ChatRoomService.validate_member(study_group, user)

        last_message = ChatMessage.objects.filter(study_group_id=study_group.id).order_by("-created_at").first()

        if last_message:
            LastReadService.update_last_read(
                study_group=study_group,
                user=user,
                message=last_message,
            )
