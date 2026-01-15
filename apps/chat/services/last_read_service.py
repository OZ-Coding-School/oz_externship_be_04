from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.chat.models.chat_message import ChatMessage
from apps.chat.models.last_read_message import LastReadMessage
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models import User


class LastReadService:
    """
    마지막 읽은 메시지를 관리하는 서비스입니다!
    - 채팅 목록에서 읽음 처리를 위해 사용함
    - 각 유저는 그룹마다 하나의 last_read_message만 가질 수 있음 (Unique Constraint)
    """

    @staticmethod
    def _validate_member(study_group: StudyGroup, user: User) -> None:
        # 해당 유저가 그룹 멤버인지 확인
        is_member = GroupMember.objects.filter(
            study_group_id=study_group.id,
            user_id=user.id,
        ).exists()

        if not is_member:
            raise PermissionDenied("그룹 멤버만 읽음 정보를 수정할 수 있습니다.")

    @staticmethod
    @transaction.atomic
    def update_last_read(
        study_group: StudyGroup,
        user: User,
        message: ChatMessage,
    ) -> LastReadMessage:
        """
        사용자가 스터디 그룹에서 마지막으로 읽은 메시지를 갱신
        """
        # 그룹 구성원이 맞는지 검증
        LastReadService._validate_member(study_group, user)

        last_read, _ = LastReadMessage.objects.update_or_create(
            study_group=study_group,
            user=user,
            defaults={"message": message},
        )
        return last_read

    @staticmethod
    def get_last_read(
        study_group: StudyGroup,
        user: User,
    ) -> LastReadMessage | None:
        """
        특정 유저가 특정 그룹에서 마지막으로 읽은 메시지를 조회함
        - 없으면 None 반환
        """
        return LastReadMessage.objects.filter(study_group=study_group, user=user).first()
