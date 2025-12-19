import asyncio
import json
import logging
from typing import Any, AsyncGenerator, TypeAlias, Union

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest, JsonResponse, StreamingHttpResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken

from apps.notification.services.pubsub_creator import notification_service
from apps.study_groups.models import GroupMember

logger = logging.getLogger(__name__)

UserType: TypeAlias = AbstractBaseUser
UserModel = get_user_model()


async def notification_stream(request: HttpRequest) -> Union[StreamingHttpResponse, JsonResponse]:
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    # 헤더에서 베어러 접두사 제거
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        return JsonResponse({"detail": "토큰이 필요합니다."}, status=401)

    try:
        auth = JWTAuthentication()
        valid_token = auth.get_validated_token(token.encode("utf-8"))
        user: Any = await sync_to_async(lambda wf: auth.get_user(wf), thread_sensitive=True)(valid_token)
        if not user or not user.is_authenticated:
            return JsonResponse({"detail": "사용자를 찾을 수 없습니다."}, status=401)
        user_id: int = user.id

    except (InvalidToken, AuthenticationFailed):
        return JsonResponse({"detail": "인증되지 않은 토큰입니다."}, status=401)

    async def async_event_stream() -> AsyncGenerator[str, None]:
        try:
            yield f"data: {json.dumps({'type':'connected'}, ensure_ascii=False)}\n\n"

            # 클라이언트가 SSE 엔드포인트에 처음 접속하면 연결 성공했다. (아무 데이터도 안오면 연결이 죽은줄 알고 타임아웃 걸어버림)
            # data: {내용}
            # (빈 줄)     << 이런 포맷임.

            # 그룹 처리. 목적은 여러 그룹들을 정리해서 밑에 인자로 넣을 거.
            groups = [
                group_id
                async for group_id in GroupMember.objects.filter(user_id=user_id).values_list(
                    "study_group_id", flat=True
                )
            ]

            # 레디스 구독 처리 - 여기서 호출해야 한다. listen처리 해놔서 계속 들으며 대기중. publish하면 캐치해옴
            async for notification in notification_service.subscribe_notification(
                user_id=user_id, group_ids=groups if groups else None
            ):
                noti = json.dumps(notification, ensure_ascii=False)
                yield f"data: {noti}\n\n"
                # 예: {"message":"알림이 알립니다.", "group_id":15}
                # SSE로는 이렇게 data: {"message":"알림이 알립니다.", "group_id":15}
        except asyncio.CancelledError:
            # 클라이언트가 연결을 끊었을 때 발생하는 정상적인 상황
            logger.info(f"User {user_id} SSE 커넥션이 클라이언트에 의해 닫혔습니다.")
            raise

        except Exception as e:
            logger.exception(f"SSE 스트림 중 예외 발생: {e}")
            yield f"data:{json.dumps({'type':'Error', 'message':str(e)}, ensure_ascii=False)}\n\n"

    response = StreamingHttpResponse(async_event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache, no-transform"
    response["Connection"] = "keep-alive"
    # Nginx 사용 시 필수 설정(버퍼링 방지)
    response["X-Accel-Buffering"] = "no"

    return response
