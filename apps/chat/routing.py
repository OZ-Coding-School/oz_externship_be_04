from django.urls import re_path

from .consumers.chat_consumer import ChatConsumer

websocket_urlpatterns = [
    re_path(r"^wss/chatrooms/(?P<group_id>[0-9a-f-]+)/?$", ChatConsumer.as_asgi()),
]
