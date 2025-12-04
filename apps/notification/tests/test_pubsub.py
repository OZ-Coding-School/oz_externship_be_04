import json
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from asgiref.sync import async_to_sync
from django.test import TestCase

from apps.notification.services.pubsub_creator import RedisPubSubService
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class RedisPubSubServiceTests(TestCase):
    service: RedisPubSubService

    def setUp(self) -> None:
        self.service = RedisPubSubService()

    def _validate_and_subscribe(self, original_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        user_id: Optional[int] = kwargs.get("user_id")
        group_id: Optional[List[int]] = kwargs.get("group_id")

        if user_id is not None and not isinstance(user_id, int):
            raise TypeError("user_id는 int여야 합니다.")
        if group_id is not None:
            if not isinstance(group_id, list) or not all(isinstance(x, int) for x in group_id):
                raise TypeError("group_id는 list[int]여야 합니다.")

        if user_id is not None:
            if not User.objects.filter(id=user_id).exists():
                raise ValueError("User가 존재하지 않습니다.")

        if group_id:
            missing = [gid for gid in group_id if not StudyGroup.objects.filter(id=gid).exists()]
            if missing:
                raise ValueError(f"Group을 찾으 수 없습니다. {missing}")

        return original_fn(*args, **kwargs)

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
        async def fake_listen() -> AsyncGenerator[Dict[str, Any], None]:
            yield {"type": "message", "data": json.dumps({"v": 999})}

        fake_pubsub.listen = fake_listen
        fake_pubsub.subscribe = AsyncMock()
        fake_pubsub.close = AsyncMock()

        with patch.object(self.service, "subscribe_notification", wraps=self.service.subscribe_notification) as wrapped:
            wrapped.side_effect = lambda *a, **kw: self._validate_and_subscribe(wrapped.original, *a, **kw)

        with patch.object(self.service.redis_client, "pubsub", return_value=fake_pubsub):
            gen = self.service.subscribe_notification(user_id=10)
            result: Dict[str, Any] = async_to_sync(gen.__anext__)()
            assert result == {"v": 999}
            fake_pubsub.subscribe.assert_called_once_with("notification:user_10")
