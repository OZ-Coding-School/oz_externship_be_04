from django.test import TestCase
from unittest.mock import AsyncMock, MagicMock
import json

from asgiref.sync import async_to_sync
from apps.notification.services.pubsub_creator import RedisPubSubService


class RedisPubSubServiceTests(TestCase):
    def setUp(self):
        self.service = RedisPubSubService()
        self.service.redis_client.publish = AsyncMock()
        self.service.redis_client.pubsub = MagicMock()

    def test_publish_notification(self):
        # 셋 업에 정의해놨는데도 assert_called_once()에 노란줄
        self.service.redis_client.publish = AsyncMock()
        self.service.redis_client = MagicMock()

        channel = "notification:user_1"
        data = {"msg": "hello"}

        # 비동기 함수 sync환경에서 실행
        async_to_sync(self.service.publish_notification)(channel, data)

        #한번만 호출되는지 확인
        self.service.redis_client.publish.assert_called_once()
        # 모든 인자를 튜플로 저장하기 때문에 [0]을 붙여 위치 인자만 가져옴( 0채널/1데이타[메시지] )
        args = self.service.redis_client.publish.call_args[0]

        self.assertEqual(args[0], channel)
        self.assertEqual(json.loads(args[1]), data)

    def test_publish_user_notification(self):
        self.service.publish_notification = AsyncMock()
        async_to_sync(self.service.publish_user_notification)(3, {"x": 1})

        self.service.publish_notification.assert_called_once()
        args = self.service.publish_notification.call_args[0]

        self.assertEqual(args[0], "notification:user_3")
        self.assertEqual(args[1], {"x": 1})

    def test_publish_group_notification(self):
        self.service.publish_notification = AsyncMock()
        async_to_sync(self.service.publish_group_notification)(7, {"y": "hi"})

        self.service.publish_notification.assert_called_once()
        args = self.service.publish_notification.call_args[0]

        self.assertEqual(args[0], "notification:group_7")
        self.assertEqual(args[1], {"y": "hi"})

    def test_subscribe_notification(self):
        # 가짜펍섭을 반환하게 함
        fake_pubsub = MagicMock()
        self.service.redis_client.pubsub.return_value = fake_pubsub

        # 메시지 계속 스트리밍하지 않고 한번만.
        async def fake_listen():
            yield {"type": "message", "data": json.dumps({"v": 999})}

        fake_pubsub.listen = fake_listen
        fake_pubsub.subscribe = AsyncMock()
        fake_pubsub.close = AsyncMock()

        gen = self.service.subscribe_notification(user_id=10)
        result = async_to_sync(gen.__anext__)()

        self.assertEqual(result, {"v": 999})
        fake_pubsub.subscribe.assert_called_once_with("notification:user_10")
