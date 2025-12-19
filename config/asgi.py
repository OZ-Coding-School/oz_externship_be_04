import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

django_asgi_app = get_asgi_application()

# 초기화 이후에 라이브러리 및 라우팅 임포트
from channels.routing import (  # type: ignore[import-untyped]
    ProtocolTypeRouter,
    URLRouter,
)

from apps.chat.routing import websocket_urlpatterns

from django_channels_jwt_auth_middleware.auth import JWTAuthMiddlewareStack  # type: ignore[import-untyped] # isort: skip


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
