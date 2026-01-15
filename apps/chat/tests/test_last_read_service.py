from django.core.exceptions import PermissionDenied
from django.test import TestCase

from apps.chat.models.chat_message import ChatMessage
from apps.chat.models.last_read_message import LastReadMessage
from apps.chat.services.last_read_service import LastReadService
from apps.study_groups.models import GroupMember, StudyGroup
from apps.users.models.users import User


class TestLastReadService(TestCase):

    def setUp(self) -> None:
        # 사용자
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

        self.group = StudyGroup.objects.create(
            name="Django Study",
            introduction="스터디 소개",
            max_headcount=5,
            start_at="2025-12-01T00:00:00Z",
            end_at="2025-12-30T00:00:00Z",
        )

        GroupMember.objects.create(
            study_group_id=self.group,
            user_id=self.user,
            is_leader=True,
        )

        self.message1 = ChatMessage.objects.create(
            study_group=self.group,
            sender=self.user,
            content="메시지 1",
        )

        self.message2 = ChatMessage.objects.create(
            study_group=self.group,
            sender=self.user,
            content="메시지 2",
        )

    def test_update_last_read_create(self) -> None:
        # 처음 읽을 경우 LastReadMessage 생성
        LastReadService.update_last_read(
            study_group=self.group,
            user=self.user,
            message=self.message1,
        )

        record = LastReadMessage.objects.filter(
            study_group=self.group,
            user=self.user,
        ).first()

        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(record.message.id, self.message1.id)

    def test_update_last_read_update(self) -> None:
        # 이미 읽은 과거가 있으면 제일 최신 메시지로 업데이트

        LastReadMessage.objects.create(
            study_group=self.group,
            user=self.user,
            message=self.message1,
        )

        LastReadService.update_last_read(
            study_group=self.group,
            user=self.user,
            message=self.message2,
        )

        updated = LastReadMessage.objects.get(
            study_group=self.group,
            user=self.user,
        )

        self.assertEqual(updated.message.id, self.message2.id)

    def test_update_last_read_fail_other_user(self) -> None:
        # 그룹 구성원이 아니라면 PermissionDenied
        with self.assertRaises(PermissionDenied):
            LastReadService.update_last_read(
                study_group=self.group,
                user=self.other_user,
                message=self.message1,
            )
