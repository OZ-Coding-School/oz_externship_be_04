import json
from typing import Any, Dict, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

from asgiref.sync import async_to_sync
from django.test import TestCase

from apps.notification.services.pubsub_creator import RedisPubSubService


class RedisPubSubServiceTests(TestCase):
    service: RedisPubSubService

    def setUp(self) -> None:
        self.service = RedisPubSubService()

    def test_publish_notification(self) -> None:
        channel: str = "notification:user_1"
        data: Dict[str, Any] = {"msg": "hello"}

        with patch.object(self.service.redis_client, "publish", new_callable=AsyncMock) as mock_publish:
            # 비동기 함수 sync환경에서 실행
            async_to_sync(self.service.publish_notification)(channel, data)

            # 한번만 호출되는지 확인
            mock_publish.assert_called_once()
            # 모든 인자를 튜플로 저장하기 때문에 [0]을 붙여 위치 인자만 가져옴( 0채널/1데이타[메시지] )
            args = mock_publish.call_args[0]

            assert args[0] == channel
            assert json.loads(args[1]) == data

    def test_publish_user_notification(self) -> None:
        data: Dict[str, Any] = {"x": 1}

        with patch.object(self.service, "publish_notification", new_callable=AsyncMock) as mock_publish:
            async_to_sync(self.service.publish_user_notification)(3, {"x": 1})

            mock_publish.assert_called_once()
            args = mock_publish.call_args[0]

            assert args[0] == "notification:user_3"
            assert args[1] == data

    def test_publish_group_notification(self) -> None:
        data: Dict[str, Any] = {"y": "hi"}

        with patch.object(self.service, "publish_notification", new_callable=AsyncMock) as mock_publish:
            async_to_sync(self.service.publish_group_notification)(7, {"y": "hi"})

            mock_publish.assert_called_once()
            args = mock_publish.call_args[0]

            assert args[0] == "notification:group_7"
            assert args[1] == data

    def test_subscribe_notification(self) -> None:
        # 가짜펍섭을 반환하게 함
        fake_pubsub: MagicMock = MagicMock()

        # 메시지 계속 스트리밍하지 않고 한번만.
        async def fake_listen()-> AsyncGenerator[Dict[str, Any], None]:
            yield {"type": "message", "data": json.dumps({"v": 999})}

        fake_pubsub.listen = fake_listen
        fake_pubsub.subscribe = AsyncMock()
        fake_pubsub.close = AsyncMock()

        with patch.object(self.service.redis_client, "pubsub", return_value=fake_pubsub):
            gen = self.service.subscribe_notification(user_id=10)
            result: Dict[str, Any] = async_to_sync(gen.__anext__)()
            assert result == {"v": 999}
            fake_pubsub.subscribe.assert_called_once_with("notification:user_10")