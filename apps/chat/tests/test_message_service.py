from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from apps.chat.models.chat_message import ChatMessage
from apps.chat.services.message_service import MessageService
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models.users import User


class TestMessageService(TestCase):

    def setUp(self) -> None:
        # 사용자 생성
        self.user = User.objects.create(
            email="test@example.com",
            name="김오즈",
            nickname="테스터",
            phone_number="01012345678",
            gender="M",
            birthday="1999-01-01",
        )

        self.other_user = User.objects.create(
            email="hayeong@example.com",
            name="송하영",
            nickname="ha0",
            phone_number="01012341234",
            gender="F",
            birthday="1997-09-29",
        )

        # 스터디 그룹 생성
        self.group = StudyGroup.objects.create(
            name="Django Study",
            introduction="스터디 소개",
            max_headcount=5,
            start_at="2025-12-01T00:00:00Z",
            end_at="2025-12-30T00:00:00Z",
        )

        # 그룹 멤버 등록
        GroupMember.objects.create(
            study_group_id=self.group,
            user_id=self.user,
            is_leader=True,
        )

    # 메시지 생성 테스트
    def test_create_message_success(self) -> None:
        """그룹 멤버는 정상적으로 메시지 생성 가능"""

        msg = MessageService.create_message(study_group=self.group, user=self.user, content="안녕하세요!")

        self.assertIsInstance(msg, ChatMessage)
        self.assertEqual(msg.content, "안녕하세요!")
        self.assertEqual(msg.sender_id, self.user.id)

    def test_create_message_fail_for_non_member(self) -> None:
        # 그룹 멤버가 아니면 PermissionDenied 발생

        with self.assertRaises(PermissionDenied):
            MessageService.create_message(study_group=self.group, user=self.other_user, content="멤버가 아닙니다")

    def test_create_message_fail_empty_content(self) -> None:
        # 빈 메시지 내용이면 ValidationError 발생

        with self.assertRaises(ValidationError):
            MessageService.create_message(study_group=self.group, user=self.user, content="   ")

    # 메시지 단일 조회 테스트
    def test_get_message_success(self) -> None:
        """단일 메시지 조회 성공"""

        msg = ChatMessage.objects.create(
            study_group=self.group,
            sender=self.user,
            content="조회 테스트",
        )

        found = MessageService.get_message(msg.id)

        self.assertEqual(found.id, msg.id)
        self.assertEqual(found.content, "조회 테스트")

    def test_get_message_not_found(self) -> None:
        # 없는 메시지를 조회하면 ValidationError 발생

        with self.assertRaises(ValidationError):
            MessageService.get_message(9999)
