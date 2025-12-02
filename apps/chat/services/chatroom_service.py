from typing import Any, Optional

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet

from apps.chat.models.chat_message import ChatMessage
from apps.chat.services.last_read_service import LastReadService
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models import User


class ChatRoomService:
    # 스터디 그룹의 채팅 조회 기능 담당

    @staticmethod
    def validate_member(study_group: StudyGroup, user: User) -> None:
        """
        요청한 사용자가 해당 그룹 구성원인지 검사
        구성원이 아니라면 PermissionDenied 예외를 강제 발생시키게끔 했습니다 !
        """
        exists = GroupMember.objects.filter(
            study_group_id=study_group.id,
            user_id=user.id,
        ).exists()

        if not exists:
            raise PermissionDenied("그룹 멤버만 채팅을 조회할 수 있습니다.")

    @staticmethod
    def get_chatrooms(user: User) -> list[dict[str, Any]]:
        # 채팅방 목록 조회
        memberships = GroupMember.objects.filter(user_id=user.id).select_related("study_group_id")

        results: list[dict[str, Any]] = []

        for member in memberships:
            group = member.study_group_id  # FK 객체

            last_message: Optional[ChatMessage] = (
                ChatMessage.objects.filter(study_group=group).order_by("-created_at").first()
            )

            last_read = LastReadService.get_last_read(group, user)

            if last_read:
                unread_count = ChatMessage.objects.filter(
                    study_group=group,
                    created_at__gt=last_read.message.created_at,
                ).count()
            else:
                unread_count = ChatMessage.objects.filter(study_group=group).count()

            results.append(
                {
                    "group_id": group.id,
                    "group_name": group.name,
                    "last_message_content": last_message.content if last_message else None,
                    "last_message_time": last_message.created_at if last_message else None,
                    "unread_count": unread_count,
                }
            )

        return results

    @staticmethod
    def get_room_info(study_group: StudyGroup, user: User) -> dict[str, Any]:
        # 채팅방 접속 시 필요한 기본 정보 조회
        ChatRoomService.validate_member(study_group, user)

        members = GroupMember.objects.filter(study_group_id=study_group.id).select_related("user_id")

        member_list = [
            {
                "nickname": m.user_id.nickname,
                "is_leader": m.is_leader,
            }
            for m in members
        ]

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

        queryset = ChatMessage.objects.filter(
            study_group=study_group,
            # 가입 이후만 보여주기
            created_at__gte=membership.created_at,
        ).select_related("sender")

        if cursor:
            queryset = queryset.filter(id__lte=cursor)

        return queryset.order_by("-id")[:limit]

    @staticmethod
    def mark_all_read(study_group: StudyGroup, user: User) -> None:
        # 채팅방 접속시 사용자가 이전에 읽지 않은 메시지를 가장 최신 메시지 기준으로 전부 읽음 처리
        ChatRoomService.validate_member(study_group, user)

        last_message = ChatMessage.objects.filter(study_group=study_group).order_by("-created_at").first()

        if last_message:
            LastReadService.update_last_read(
                study_group=study_group,
                user=user,
                message=last_message,
            )
