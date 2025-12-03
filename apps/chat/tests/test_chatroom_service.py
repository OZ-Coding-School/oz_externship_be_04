import time

from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.chat.models.chat_message import ChatMessage
from apps.chat.models.last_read_message import LastReadMessage
from apps.chat.services.chatroom_service import ChatRoomService
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models.users import User


class TestChatRoomService(TestCase):

    def setUp(self) -> None:
        # 사용자
        self.user = User.objects.create(
            email="user@example.com",
            name="김오즈",
            nickname="테스트",
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

        # 스터디 그룹
        self.group = StudyGroup.objects.create(
            name="Django Study",
            introduction="스터디 소개",
            max_headcount=5,
            start_at="2025-12-01T00:00:00Z",
            end_at="2025-12-30T00:00:00Z",
        )

        # user만 그룹 멤버로 등록
        GroupMember.objects.create(
            study_group_id=self.group,
            user_id=self.user,
            is_leader=True,
        )

        # 테스트용 메시지 생성
        self.msg1 = ChatMessage.objects.create(
            study_group=self.group,
            sender=self.user,
            content="첫 번째 메시지",
        )
        time.sleep(0.001)  # 생성 시간 차이를 내려고 넣었습니다

        self.msg2 = ChatMessage.objects.create(
            study_group=self.group,
            sender=self.user,
            content="두 번째 메시지",
        )

    # 멤버 검증 테스트
    def test_validate_member_success(self) -> None:
        # 그룹에 속한 사용자는 검증 통과
        ChatRoomService.validate_member(self.group, self.user)

    def test_validate_member_fail(self) -> None:
        # 그룹에 속하지 않은 사용자는 PermissionDenied
        with self.assertRaises(PermissionDenied):
            ChatRoomService.validate_member(self.group, self.other_user)

    def test_get_messages(self) -> None:
        # 해당 그룹의 메시지 목록을 시간순으로 반환
        messages = ChatRoomService.get_messages(self.group, self.user)
        self.assertEqual(messages.count(), 2)

    def test_get_room_info(self) -> None:
        info = ChatRoomService.get_room_info(self.group, self.user)
        self.assertEqual(info["group_id"], self.group.id)
        self.assertEqual(len(info["members"]), 1)
        self.assertEqual(info["members"][0]["nickname"], self.user.nickname)

    def test_mark_all_read(self) -> None:
        ChatRoomService.mark_all_read(self.group, self.user)

        record = LastReadMessage.objects.get(
            study_group=self.group,
            user=self.user,
        )
        self.assertEqual(record.message.id, self.msg2.id)

    def test_mark_all_read_no_messages(self) -> None:
        # 메시지가 전혀 없는 새로운 그룹 생성
        empty_group = StudyGroup.objects.create(
            name="Empty Group",
            introduction="메시지 없음",
            max_headcount=5,
            start_at="2025-12-01T00:00:00Z",
            end_at="2025-12-30T00:00:00Z",
        )

        GroupMember.objects.create(
            study_group_id=empty_group,
            user_id=self.user,
            is_leader=True,
        )

        # 실행
        ChatRoomService.mark_all_read(empty_group, self.user)

        # 메시지가 없으면 last_read 레코드도 x
        record = LastReadMessage.objects.filter(
            study_group=empty_group,
            user=self.user,
        ).first()

        self.assertIsNone(record)

    def test_get_chatrooms_basic(self) -> None:
        # 채팅방 목록 조회 기본 테스트
        result = ChatRoomService.get_chatrooms(self.user)

        self.assertEqual(len(result), 1)

        room = result[0]

        # 그룹 id 검증
        self.assertEqual(room["group_id"], self.group.id)

        # 그룹 이름 검증
        self.assertEqual(room["group_name"], self.group.name)

        # last_read x -> unread count = 전체 메시지 개수
        total_messages = ChatMessage.objects.filter(study_group=self.group).count()

        self.assertEqual(room["unread_count"], total_messages)

    def test_get_chatrooms_with_last_read(self) -> None:
        LastReadMessage.objects.create(
            study_group=self.group,
            user=self.user,
            message=self.msg1,
        )

        result = ChatRoomService.get_chatrooms(self.user)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["unread_count"], 1)
