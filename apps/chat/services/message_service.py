from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError

from apps.chat.models import ChatMessage
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models import User


class MessageService:
    # 메시지 생성 및 단건 조회 기능 제공

    @staticmethod
    def validate_member(study_group: StudyGroup, user: User) -> None:
        # 해당 사용자가 그룹 구성원이 맞는지 검증
        is_member = GroupMember.objects.filter(
            study_group_id=study_group.id,
            user_id=user.id,  # mypy 오류로 user 대신 user.id를 넘겼습니다.
        ).exists()

        if not is_member:
            raise PermissionDenied("그룹 멤버만 메시지를 작성할 수 있습니다.")

    @staticmethod
    def create_message(
        study_group: StudyGroup,
        user: User,
        content: str,
    ) -> ChatMessage:

        if not content or not content.strip():
            raise ValidationError("메시지 내용은 비어 있을 수 없습니다.")

        MessageService.validate_member(study_group, user)

        try:
            return ChatMessage.objects.create(
                study_group=study_group,
                sender=user,
                content=content.strip(),
            )
        except IntegrityError:
            raise ValidationError("메시지를 생성할 수 없습니다.")

    @staticmethod
    def get_message(message_id: int) -> ChatMessage:
        msg = ChatMessage.objects.select_related("sender").filter(id=message_id).first()

        if msg is None:
            raise ValidationError("메시지를 찾을 수 없습니다.")

        return msg
