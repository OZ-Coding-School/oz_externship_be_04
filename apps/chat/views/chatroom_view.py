from typing import cast

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import permissions, serializers
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.serializers.chatroom_serializer import ChatroomSerializer
from apps.chat.serializers.response_serializer import (
    ErrorResponseSerializer,
    MarkAllReadResponseSerializer,
)
from apps.chat.services.chatroom_service import ChatRoomService
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class ChatRoomListView(APIView):
    # 사용자가 참여한 채팅방 목록 조회 기능
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["chat"],
        summary="채팅방 목록 조회 API",
        responses={
            200: inline_serializer(
                name="ChatRoomListResponse",
                fields={
                    "next": serializers.CharField(allow_null=True),
                    "previous": serializers.CharField(allow_null=True),
                    "results": ChatroomSerializer(many=True),
                },
            ),
            401: ErrorResponseSerializer,
        },
    )
    def get(self, request: Request) -> Response:
        user = cast(User, request.user)

        rooms = ChatRoomService.get_chatrooms(user)

        return Response(
            {
                "next": None,
                "previous": None,
                "results": rooms,
            }
        )


class ChatRoomDetailView(APIView):
    # 특정 스터디 그룹의 상세 정보 조회(그룹 채팅방)
    # 참여자 목록, 그룹 정보 반환
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["chat"],
        summary="채팅방 정보 조회 API",
        responses={
            200: ChatroomSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
        },
    )
    def get(self, request: Request, group_id: int) -> Response:
        user = cast(User, request.user)

        try:
            group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            raise NotFound("해당 채팅방을 찾을 수 없습니다.")

        # 사용자 멤버십 검증
        ChatRoomService.validate_member(group, user)

        data = ChatRoomService.get_room_info(group, user)

        return Response(
            {
                "id": data["group_id"],
                "name": data["group_name"],
                "members": data["members"],
            }
        )


class ChatRoomMarkAllReadView(APIView):
    # 사용자가 특정 채팅방의 모든 메시지를 읽음 처리
    # LastReadMessage 테이블에 마지막에 읽은 메시지 기록
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["chat"],
        summary="채팅방 읽음 처리 API",
        responses={
            200: MarkAllReadResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def post(self, request: Request, group_id: int) -> Response:
        user = cast(User, request.user)

        try:
            group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            raise NotFound("해당 채팅방을 찾을 수 없습니다.")

        # 사용자 멤버십 검증
        ChatRoomService.validate_member(group, user)

        ChatRoomService.mark_all_read(group, user)

        return Response({"detail": "채팅 읽음 처리에 성공하였습니다."})
