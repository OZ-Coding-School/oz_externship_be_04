from django.urls import path

from apps.chat.views.chatroom_view import (
    ChatRoomDetailView,
    ChatRoomListView,
    ChatRoomMarkAllReadView,
)
from apps.chat.views.message_view import (
    ChatRoomMessageListView,
    MessageCreateView,
    MessageDetailView,
)

urlpatterns = [
    # 채팅방 목록 조회
    path(
        "chatrooms/",
        ChatRoomListView.as_view(),
        name="api_v1_chatrooms_list",
    ),
    # 채팅방 상세 조회
    path(
        "chatrooms/<int:group_id>/",
        ChatRoomDetailView.as_view(),
        name="api_v1_chatrooms_retrieve",
    ),
    # 채팅방 읽음 처리
    path(
        "chatrooms/<int:group_id>/read/",
        ChatRoomMarkAllReadView.as_view(),
        name="api_v1_chatrooms_mark_all_read",
    ),
    # 멤버별 읽음 처리 API
    path(
        "chatroom/<int:group_id>/members/<int:member_id>/read/",
        ChatRoomMarkAllReadView.as_view(),
        name="api_v1_chatrooms_mark_all_read_v2",
    ),
    # 메시지 목록 조회
    path(
        "chatrooms/<int:group_id>/messages/",
        ChatRoomMessageListView.as_view(),
        name="api_v1_chatroom_message_list",
    ),
    # 메시지 생성
    path(
        "chatrooms/<int:group_id>/messages/create/",
        MessageCreateView.as_view(),
        name="api_v1_chatroom_message_create",
    ),
    # 메시지 단건 조회
    path(
        "messages/<int:message_id>/",
        MessageDetailView.as_view(),
        name="api_v1_messages_retrieve",
    ),
]
