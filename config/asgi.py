"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from channels.routing import (  # type: ignore[import-untyped]
    ProtocolTypeRouter,
    URLRouter,
)
from django.core.asgi import get_asgi_application
from django_channels_jwt_auth_middleware.auth import JWTAuthMiddlewareStack  # type: ignore

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")  # 로컬 테스트용 .local 삭제

django_asgi_app = get_asgi_application()

from apps.chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
