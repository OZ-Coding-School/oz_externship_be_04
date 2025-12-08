import json
from typing import Any, AsyncGenerator, AsyncIterable, Iterable, Optional, Union
from unittest.mock import MagicMock, patch

from asgiref.sync import async_to_sync
from django.http import JsonResponse, StreamingHttpResponse
from django.test import RequestFactory, TestCase
from rest_framework_simplejwt.exceptions import InvalidToken

from apps.notification.views.sse_views import notification_stream
from apps.users.models import User


# 헬퍼 함수
def collect_streaming_content(content: Union[Iterable[Any], AsyncIterable[Any]]) -> list[Any]:
    if hasattr(content, "__aiter__"):

        async def inner() -> list[Any]:
            return [item async for item in content]

        return async_to_sync(inner)()
    else:
        return list(content)


class SSEViewStreamTests(TestCase):
    factory: RequestFactory

    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_no_token(self) -> None:
        request = self.factory.get("/stream")
        response = async_to_sync(notification_stream)(request)

        assert isinstance(response, JsonResponse)
        assert response.status_code == 401
        body = json.loads(response.content.decode())
        assert body["detail"] == "토큰이 필요합니다."

    @patch("apps.notification.views.sse_views.JWTAuthentication")
    def test_invalid_token(self, mock_jwt_auth_cls: MagicMock) -> None:
        mock_auth = MagicMock()
        mock_auth.get_validated_token.side_effect = InvalidToken("잘못된 토큰")
        mock_jwt_auth_cls.return_value = mock_auth

        request = self.factory.get("/stream", {"token": "잘못된 토큰"})
        response = async_to_sync(notification_stream)(request)

        assert isinstance(response, JsonResponse)
        assert response.status_code == 401
        body = json.loads(response.content.decode())
        assert body["detail"] == "인증되지 않은 토큰입니다."

    # @patch("모듈.A")
    # @patch("모듈.B")
    # def test_x(self, mock_b, mock_a):
    @patch("apps.notification.views.sse_views.notification_service")
    @patch("apps.notification.views.sse_views.JWTAuthentication")
    def test_valid_token(self, mock_jwt_auth_cls: MagicMock, mock_notification_service: MagicMock) -> None:
        user = User(
            email="u@example.com",
            name="테스트",
            nickname="TestNick",
            phone_number="01012341234",
            gender="M",
            birthday="1392-01-23",
            profile_img_url="https://example.com/profile.png",
            is_active=True,
        )
        user.set_password("pw1234")
        user.save()
        # get_validated_token 정상 반환, get_user는 DB 유저 반환
        mock_auth = MagicMock()
        mock_auth.get_validated_token.return_value = {"token": "정상적인 토큰"}
        mock_auth.get_user.return_value = user
        mock_jwt_auth_cls.return_value = mock_auth

        # 유효한 토큰으로 들어온 요청이 SSE 뷰에서 스트리밍을 시작하는지,
        # 스트리밍 첫 번째 메시지('connected')가 제대로 나오도록
        # subscribe_notification 을 Mock 으로 교체해 테스트
        async def fake_subscribe_notification(
            _user_id: Optional[Any] = None, _group_ids: Optional[Any] = None
        ) -> AsyncGenerator[Any, None]:
            yield {"type": "connected"}

        # 가짜 async generator를 만들어 넣는데, 조건 : async함수일 것. 내부에 yield가 있을 것

        mock_notification_service.subscribe_notification.side_effect = fake_subscribe_notification

        request = self.factory.get("/stream", {"token": "ValidToken"})
        response = async_to_sync(notification_stream)(request)

        assert isinstance(response, StreamingHttpResponse)

        assert response["content-type"].startswith("text/event-stream")

        # StreamingHttpResponse는 전체 응답을 한 번에 반환하지 않는다. chunk 단위로 흘려보냄.
        chunks = collect_streaming_content(response.streaming_content)
        chunks = [c.decode() if isinstance(c, bytes) else str(c) for c in chunks]
        full = "".join(chunks)
        assert "connected" in full
