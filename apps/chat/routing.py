from django.urls import re_path

from .consumers.chat_consumer import ChatConsumer

websocket_urlpatterns = [
    re_path(r"^wss/chatrooms/(?P<group_id>\d+)/?$", ChatConsumer.as_asgi()),
]
