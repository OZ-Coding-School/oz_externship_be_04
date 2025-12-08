import json
import logging
from typing import Any, AsyncGenerator, Dict, Optional

from django.conf import settings
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisPubSubService:
    def __init__(self) -> None:
        # Redis 클라이언트 연결함
        redis_url = getattr(settings, "CACHES", {}).get("default", {}).get("LOCATION")
        if not redis_url:
            raise RuntimeError("REDIS URL을 찾지 못했습니다. : settings.CACHES['default']['LOCATION']")
        self.redis_client: Redis = Redis.from_url(redis_url)

    def get_user_channel(self, user_id: int) -> str:
        # 사용자 알림 채널
        return f"notification:user_{user_id}"

    def get_group_channel(self, group_id: int) -> str:
        # 그룹 알림 채널
        return f"notification:group_{group_id}"

    async def publish_notification(self, channel: str, data: Dict[str, Any]) -> None:
        try:
            message = json.dumps(data, ensure_ascii=False, default=str)
            # 아스키 하지말고 날짜 또는 숫자도 str 취급해서 덤프해라
        except Exception as e:
            logger.exception(f"데이터 JSON으로 직렬화 실패 ㅠㅠ {e}")
            raise
        try:
            await self.redis_client.publish(channel, message)
            logger.info(f"{channel}채널에 {message} 알림")
        except Exception as e:
            logger.exception(f"{channel} 퍼블리쉬 중 예외 발생 {e}")
            raise

    async def publish_user_notification(self, user_id: int, notification_data: Dict[str, Any]) -> None:
        await self.publish_notification(self.get_user_channel(user_id), notification_data)

    async def publish_group_notification(self, group_id: int, notification_data: Dict[str, Any]) -> None:
        await self.publish_notification(self.get_group_channel(group_id), notification_data)

    # 채널 구독 및 메시지 스트리밍
    async def subscribe_notification(
        self, user_id: Optional[int] = None, group_ids: Optional[list[int]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not user_id and not group_ids:
            raise ValueError("유저 또는 그룹 중 최소 하나 이상이 필요합니다.")
        channels = []
        if user_id:
            channels.append(self.get_user_channel(user_id))
        # 복수의 그룹도 처리할 수 있게끔 수정
        if group_ids:
            for gid in group_ids:
                channels.append(self.get_group_channel(gid))

        pubsub = self.redis_client.pubsub()
        try:
            await pubsub.subscribe(*channels)
            logger.info(f"redis 채널을 구독합니다: {channels}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield data
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.exception(f"메시지 디코드가 실패했습니다. {channels}:{e}")

        except Exception as e:
            logger.exception(f"레디스 구독 에러:{e}")
        finally:
            try:
                await pubsub.close()
            except Exception:
                pass


notification_service: RedisPubSubService = RedisPubSubService()
