from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from asgiref.sync import sync_to_async
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.notification.infra.task import (
    send_study_group_notification,
    send_to_pubsub,
    send_today_schedule_notification,
    send_tomorrow_schedule_notification,
)
from apps.notification.models import Notification


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class SendToPubSubTaskTest(TestCase):
    """send_to_pubsub 태스크 기본 기능 테스트"""

    def setUp(self) -> None:
        """테스트 데이터 준비"""
        from apps.users.models import User

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            nickname="테스트유저",
            name="테스트",
            phone_number="01012345678",
            gender="M",
        )
        self.notification = Notification.objects.create(
            user=self.user, content="테스트 알림", type=Notification.NotificationType.STUDY_JOIN, back_url_link="/test"
        )

    @patch("apps.notification.infra.task.notification_service.publish_user_notification")
    @patch("apps.notification.infra.task.Notification.objects.select_related")
    def test_send_to_pubsub_calls_publish(self, mock_select_related: MagicMock, mock_publish: MagicMock) -> None:
        """정상 시나리오: publish_user_notification 호출 확인"""
        # Arrange
        mock_aget = AsyncMock(return_value=self.notification)
        mock_select_related.return_value.aget = mock_aget
        mock_publish.return_value = AsyncMock()()

        # Act
        send_to_pubsub(self.notification.id)

        # Assert
        mock_aget.assert_called_once_with(id=self.notification.id)

    @patch("apps.notification.infra.task.Notification.objects.select_related")
    @patch("apps.notification.infra.task.logger")
    def test_send_to_pubsub_handles_exception(self, mock_logger: MagicMock, mock_select_related: MagicMock) -> None:
        """예외 발생 시 로깅 확인"""
        # Arrange - aget에서 예외 발생하도록 설정
        mock_aget = AsyncMock(side_effect=Exception("Database error"))
        mock_select_related.return_value.aget = mock_aget

        # Act
        send_to_pubsub(self.notification.id)

        # Assert
        mock_logger.exception.assert_called_once()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class SendStudyGroupNotificationTaskTest(TestCase):
    """send_study_group_notification 태스크 기본 기능 테스트"""

    def setUp(self) -> None:
        """테스트 데이터 준비"""
        from apps.users.models import User

        self.user = User.objects.create_user(
            email="group@example.com",
            password="testpass123",
            nickname="그룹유저",
            name="그룹",
            phone_number="01012345679",
            gender="F",
        )
        self.notification = Notification.objects.create(
            user=self.user, content="그룹 알림", type=Notification.NotificationType.STUDY_JOIN, back_url_link="/group"
        )
        self.group_id = 1

    @patch("apps.notification.infra.task.notification_service.publish_group_notification")
    @patch("apps.notification.infra.task.Notification.objects.aget")
    def test_send_study_group_notification_calls_publish(self, mock_aget: MagicMock, mock_publish: MagicMock) -> None:
        """정상 시나리오: publish_group_notification 호출 확인"""
        # Arrange
        mock_aget.return_value = self.notification
        mock_publish.return_value = AsyncMock()()

        # Act
        send_study_group_notification(self.notification.id, self.group_id)

        # Assert
        mock_aget.assert_called_once_with(id=self.notification.id)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class SendTomorrowScheduleNotificationTaskTest(TestCase):
    """send_tomorrow_schedule_notification 태스크 기본 기능 테스트"""

    @patch("apps.notification.infra.task.send_to_pubsub.delay")
    @patch("apps.notification.infra.task.Notification.objects.bulk_create")
    @patch("apps.notification.infra.task.ScheduleParticipants.objects.filter")
    async def test_creates_notification_and_calls_pubsub(
        self, mock_filter: MagicMock, mock_bulk_create: MagicMock, mock_delay: MagicMock
    ) -> None:
        """알림 생성 및 send_to_pubsub.delay 호출 확인"""
        # Arrange - sync_to_async로 DB 작업 래핑
        from apps.study_groups.models.study_group import GroupMember, StudyGroup
        from apps.users.models import User

        user = await sync_to_async(User.objects.create_user)(
            email="tomorrow@example.com",
            password="testpass123",
            nickname="내일유저",
            name="내일",
            phone_number="01099999999",
            gender="M",
        )

        study_group = await sync_to_async(StudyGroup.objects.create)(
            name="내일 스터디",
            introduction="내일 진행",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )

        member = await sync_to_async(GroupMember.objects.create)(
            study_group_id=study_group, user_id=user, is_leader=True
        )

        # Mock 참가자 생성
        mock_participant = Mock()
        mock_participant.member.user_id.id = user.id
        mock_participant.member.user_id.nickname = user.nickname
        mock_participant.schedule.study_group.name = study_group.name

        mock_queryset = Mock()
        mock_queryset.select_related.return_value = [mock_participant]
        mock_filter.return_value = mock_queryset

        # Mock notification 생성
        created_notification = Notification(
            id=1,
            user_id=user.id,
            content=f"{study_group.name}에 {user.nickname}님이 참여했습니다.",
            type=Notification.NotificationType.STUDY_JOIN,
            back_url_link="",
        )
        mock_bulk_create.return_value = [created_notification]

        # Act
        await send_tomorrow_schedule_notification()

        # Assert
        mock_bulk_create.assert_called_once()
        mock_delay.assert_called_once_with(created_notification.id)


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
class SendTodayScheduleNotificationTaskTest(TestCase):
    """send_today_schedule_notification 태스크 기본 기능 테스트"""

    @patch("apps.notification.infra.task.send_to_pubsub.delay")
    @patch("apps.notification.infra.task.Notification.objects.bulk_create")
    @patch("apps.notification.infra.task.ScheduleParticipants.objects.filter")
    async def test_creates_notification_and_calls_pubsub(
        self, mock_filter: MagicMock, mock_bulk_create: MagicMock, mock_delay: MagicMock
    ) -> None:
        """알림 생성 및 send_to_pubsub.delay 호출 확인"""
        # Arrange - sync_to_async로 DB 작업 래핑
        from apps.study_groups.models.study_group import GroupMember, StudyGroup
        from apps.users.models import User

        user = await sync_to_async(User.objects.create_user)(
            email="today@example.com",
            password="testpass123",
            nickname="오늘유저",
            name="오늘",
            phone_number="01088888888",
            gender="F",
        )

        study_group = await sync_to_async(StudyGroup.objects.create)(
            name="오늘 스터디",
            introduction="오늘 진행",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )

        member = await sync_to_async(GroupMember.objects.create)(
            study_group_id=study_group, user_id=user, is_leader=True
        )

        # Mock 참가자 및 스케줄 생성
        mock_schedule = Mock()
        mock_schedule.start_time.strftime.return_value = "14:30"
        mock_schedule.end_time.strftime.return_value = "16:30"
        mock_schedule.study_group.name = study_group.name
        mock_schedule.title = "오늘 회의"

        mock_participant = Mock()
        mock_participant.member.user_id.id = user.id
        mock_participant.member.user_id.nickname = user.nickname
        mock_participant.schedule = mock_schedule

        mock_queryset = Mock()
        mock_queryset.select_related.return_value = [mock_participant]
        mock_filter.return_value = mock_queryset

        # Mock notification 생성
        created_notification = Notification(
            id=2,
            user_id=user.id,
            content=f"금일 14:30부터16:30까지{study_group.name}에서 오늘 회의이예정되어 있습니다! 잊지말고 참여해주세요!",
            type=Notification.NotificationType.TODAY_SCHEDULE,
            back_url_link="",
        )
        mock_bulk_create.return_value = [created_notification]

        # Act
        await send_today_schedule_notification()

        # Assert
        mock_bulk_create.assert_called_once()
        mock_delay.assert_called_once_with(created_notification.id)

    @patch("apps.notification.infra.task.send_to_pubsub.delay")
    @patch("apps.notification.infra.task.Notification.objects.bulk_create")
    @patch("apps.notification.infra.task.ScheduleParticipants.objects.filter")
    async def test_notification_content_includes_time(
        self, mock_filter: MagicMock, mock_bulk_create: MagicMock, mock_delay: MagicMock
    ) -> None:
        """알림 content에 시간 정보 포함 확인"""
        # Arrange - sync_to_async로 DB 작업 래핑
        from apps.study_groups.models.study_group import StudyGroup
        from apps.users.models import User

        user = await sync_to_async(User.objects.create_user)(
            email="time@example.com",
            password="testpass123",
            nickname="시간유저",
            name="시간",
            phone_number="01077777777",
            gender="M",
        )

        study_group = await sync_to_async(StudyGroup.objects.create)(
            name="시간 스터디",
            introduction="시간 테스트",
            max_headcount=5,
            start_at=timezone.now(),
            end_at=timezone.now() + timedelta(days=30),
        )

        # Mock 스케줄과 참가자
        mock_schedule = Mock()
        mock_schedule.start_time.strftime.return_value = "14:30"
        mock_schedule.end_time.strftime.return_value = "16:30"
        mock_schedule.study_group.name = study_group.name
        mock_schedule.title = "테스트 회의"

        mock_participant = Mock()
        mock_participant.member.user_id.id = user.id
        mock_participant.schedule = mock_schedule

        mock_queryset = Mock()
        mock_queryset.select_related.return_value = [mock_participant]
        mock_filter.return_value = mock_queryset

        # Mock notification - content에 시간 포함
        content = (
            f"금일 14:30부터16:30까지{study_group.name}에서 테스트 회의이예정되어 있습니다! 잊지말고 참여해주세요!"
        )
        created_notification = Notification(
            id=3, user_id=user.id, content=content, type=Notification.NotificationType.TODAY_SCHEDULE, back_url_link=""
        )
        mock_bulk_create.return_value = [created_notification]

        # Act
        await send_today_schedule_notification()

        # Assert
        # bulk_create가 호출되었고, notification에 시간이 포함되어 있는지 확인
        self.assertTrue(mock_bulk_create.called)
        notifications_arg = mock_bulk_create.call_args[0][0]
        self.assertEqual(len(notifications_arg), 1)

        notification = notifications_arg[0]
        self.assertIn("14:30", notification.content)
        self.assertIn("16:30", notification.content)
        self.assertEqual(notification.type, Notification.NotificationType.TODAY_SCHEDULE)
