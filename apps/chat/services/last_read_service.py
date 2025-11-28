from django.db import transaction

from apps.chat.models.chat_message import ChatMessage
from apps.chat.models.last_read_message import LastReadMessage
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class LastReadService:
    """
    마지막 읽은 메시지를 관리하는 서비스입니다!
    - 채팅 목록에서 읽음 처리를 위해 사용함
    - 각 유저는 그룹마다 하나의 last_read_message만 가질 수 있음 (Unique Constraint)
    """

    @staticmethod
    @transaction.atomic
    def update_last_read(
        study_group: StudyGroup,
        user: User,
        message: ChatMessage,
    ) -> LastReadMessage:
        """
        사용자가 스터디 그룹에서 마지막으로 읽은 메시지를 갱신합니다

        동작 방식
        - 동일한 (study_group, user) 조합은 하나만 존재해야 하므로 update_or_create 사용
        - 동시에 여러 요청이 올라와도 atomic 처리로 race condition 방지
        """
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
