import asyncio
from datetime import date, datetime, timezone

from apps.core.utils.isolated_cache_testcase import IsolatedRedisTestClient
from apps.notification.infra.task import send_study_group_notification, send_to_pubsub
from apps.notification.models import Notification
from apps.notification.services.pubsub_creator import (
    RedisPubSubService,
    notification_service,
)
from apps.study_groups.models import StudyGroup
from apps.users.models import User
from apps.users.models.users import GenderChoices


class TasksTest(IsolatedRedisTestClient):
    def setUp(self) -> None:
        super().setUp()

        self.user = User.objects.create_user(
            email="test@test.com",
            nickname="test12",
            name="유저1",
            password="password123",
            phone_number="010-1234-5679",
            birthday=date(1995, 1, 11),
            gender=GenderChoices.MALE,
        )

        self.notification = Notification.objects.create(
            user=self.user,
            content="테스트 알림",
            type=Notification.NotificationType.ADD_APPLICATION,
            back_url_link="https://example.com/test",
        )

        self.study_group = StudyGroup.objects.create(
            name="오즈코딩",
            introduction="파이썬 기초",
            max_headcount=5,
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc),
        )

    async def test_send_to_pubsub(
        self,
    ) -> None:
        """to redis 알림 전송 테스트"""
        messages = []

        async def message_listener() -> None:
            async for message in notification_service.subscribe_notification(user_id=self.user.id):
                messages.append(message)
                if len(messages) >= 1:
                    break

        listener_task = asyncio.create_task(message_listener())  # type: ignore[unused-ignore]

        await asyncio.sleep(0.1)

        send_to_pubsub(self.notification.id)

        try:
            await listener_task
        except asyncio.TimeoutError:
            listener_task.cancel()

        self.assertEqual(len(messages), 1)
        data = messages[0]
        self.assertEqual(data["id"], self.notification.id)
        self.assertEqual(data["type"], self.notification.type)
        self.assertEqual(data["content"], self.notification.content)

        await notification_service.redis_client.close()

    async def test_send_study_group_(self) -> None:
        """to redis 그룹 알림 전송 테스트"""
        notification_pubsub = RedisPubSubService()
        messages = []

        async def group_message_listener() -> None:
            async for message in notification_service.subscribe_notification(user_id=self.user.id):
                messages.append(message)
                if len(messages) >= 1:
                    break

            listener_task = asyncio.create_task(group_message_listener())

            await asyncio.sleep(1.0)

            send_study_group_notification(self.notification.id, str(self.study_group.id))

            try:
                await listener_task
            except asyncio.TimeoutError:
                listener_task.cancel()
