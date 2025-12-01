from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet

from apps.chat.models.chat_message import ChatMessage
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
            user_id=user.id,  # mypy 오류로 user 대신 user.id를 넘겼습니다.
        ).exists()

        # 스터디 그룹 비회원이면 채팅방 접근 금지
        if not exists:
            raise PermissionDenied("그룹 멤버만 채팅을 조회할 수 있습니다.")

    @staticmethod
    def get_messages(study_group: StudyGroup) -> QuerySet[ChatMessage]:
        # 특정 스터디 그룹의 메시지 목록 조회

        return ChatMessage.objects.filter(study_group=study_group).select_related("sender").order_by("created_at")
