import asyncio
import logging
from datetime import date, timedelta

from celery import shared_task  # type: ignore

from apps.notification.models import Notification
from apps.notification.services.pubsub_creator import notification_service
from apps.study_groups.models.schedule import ScheduleParticipants

logger = logging.getLogger(__name__)


@shared_task(async_=True)  # type: ignore[misc]
def send_to_pubsub(notification_id: int) -> None:
    async def _async_task() -> None:
        try:
            notification = await Notification.objects.select_related("user").aget(id=notification_id)

            await notification_service.publish_user_notification(
                user_id=notification.user.id,
                notification_data={
                    "id": notification.id,
                    "type": notification.type,
                    "content": notification.content,
                    "back_url_link": notification.back_url_link,
                    "created_at": notification.created_at.isoformat(),
                    "is_read": notification.is_read,
                },
            )
        except Exception as e:
            logger.exception(f"개인 알림 Redis publish 실패: {e}")

    try:
        event_loop = asyncio.get_event_loop()
    except RuntimeError:
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)

    if event_loop.is_running():
        asyncio.create_task(_async_task())
    else:
        event_loop.run_until_complete(_async_task())


@shared_task  # type: ignore[misc]
def send_study_group_notification(notification_id: int, group_id: int) -> None:
    async def _async_task() -> None:
        try:
            notification = await Notification.objects.aget(id=notification_id)

            notification_data = {
                "id": notification.id,
                "type": notification.type,
                "content": notification.content,
                "back_ulr_link": notification.back_url_link,
                "create_at": notification.created_at,
                "is_read": notification.is_read,
            }
            await notification_service.publish_group_notification(
                group_id=group_id, notification_data=notification_data
            )
        except Exception as e:
            logging.error(f"스터디 그룹 알림 발송 오류:{e}")

    try:
        event_loop = asyncio.get_event_loop()
    except RuntimeError:
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)

    if event_loop.is_running():
        asyncio.create_task(_async_task())
    else:
        event_loop.run_until_complete(_async_task())


@shared_task(name="send_tomorrow_schedule_notifications")  # type: ignore[misc]
async def send_tomorrow_schedule_notification() -> None:
    """예정 스케줄 알림 생성 및 배치 작업"""
    try:
        tomorrow = date.today() + timedelta(days=1)

        participanes = ScheduleParticipants.objects.filter(schedule__session_date__date=tomorrow).select_related(
            "schedule", "schedule__study_group", "member__user"
        )

        notifications = [
            Notification(
                user_id=participant.member.user_id.id,
                content=f"{participant.schedule.study_group.name}에 {participant.member.user_id.nickname}님이 참여했습니다.",
                type=Notification.NotificationType.STUDY_JOIN,
                back_url_link="",
            )
            for participant in participanes
        ]

        created_notifications = Notification.objects.bulk_create(notifications)

        for notification in created_notifications:
            send_to_pubsub.delay(notification.id)

    except Exception as e:
        logger.error(f"예정 스케줄 알림 테스크 오류: {e}")


@shared_task(name="send_today_schedule_notifications")  # type: ignore[misc]
async def send_today_schedule_notification() -> None:
    """당일 스케줄 알림 생성"""
    try:
        today = date.today()

        participans = ScheduleParticipants.objects.filter(schedule__session_date__date=today).select_related(
            "schedule", "schedule__study_group", "member__user"
        )
        notifications = [
            Notification(
                user_id=participant.member.user_id.id,
                content=f"rmadlf {participant.schedule.start_time.strftime('%H:%M')}부터"
                f"{participant.schedule.end_time.strftime('%H:%M')}까지"
                f"{participant.schedule.study_group.name}에서 {participant.schedule.title}이"
                f"에정되어 있습니다! 잊지말고 참여해주세요!",
                type=Notification.NotificationType.TODAY_SCHEDULE,
                back_url_link="",
            )
            for participant in participans
        ]

        created_notifications = Notification.objects.bulk_create(notifications)

        for notification in created_notifications:
            send_to_pubsub.delay(notification.id)

    except Exception as e:
        logger.error(f"금일 스케줄 알림 전송 오류:{e}")
