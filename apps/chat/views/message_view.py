from typing import cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.pagination import ChatRoomCursorPagination
from apps.chat.serializers.message_serializer import (
    MessageCreateRequestSerializer,
    MessageSerializer,
)
from apps.chat.serializers.response_serializer import ErrorResponseSerializer
from apps.chat.services.chatroom_service import ChatRoomService
from apps.chat.services.message_service import MessageService
from apps.study_groups.models import StudyGroup
from apps.users.models import User


class ChatRoomMessageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["chat"],
        summary="특정 채팅방의 메시지 목록 조회 API",
        parameters=[
            OpenApiParameter(name="cursor", type=OpenApiTypes.STR, location=OpenApiParameter.QUERY),
            OpenApiParameter(name="page_size", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY),
        ],
        responses={
            200: MessageSerializer(many=True),
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def get(self, request: Request, group_id: int) -> Response:
        user = cast(User, request.user)

        try:
            group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            raise NotFound("해당 채팅방을 찾을 수 없습니다.")

        # 그룹 멤버십 검증
        ChatRoomService.validate_member(group, user)

        cursor_str = request.query_params.get("cursor")
        cursor = int(cursor_str) if cursor_str and cursor_str.isdigit() else None

        qs = ChatRoomService.get_messages(
            study_group=group,
            user=user,
            cursor=cursor,
            limit=int(request.query_params.get("page_size", 100)),
        )

        paginator = ChatRoomCursorPagination()
        page = paginator.paginate_queryset(qs, request)

        serializer = MessageSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MessageCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["chat"],
        summary="메시지 생성 API",
        request=MessageCreateRequestSerializer,
        responses={
            201: MessageSerializer,
            400: ErrorResponseSerializer,
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

        # 그룹 멤버십 검증
        ChatRoomService.validate_member(group, user)

        serializer = MessageCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = MessageService.create_message(
            study_group=group,
            user=user,
            content=serializer.validated_data["content"],
        )

        return Response(MessageSerializer(message).data, status=201)


class MessageDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["chat"],
        summary="메시지 상세 조회 API",
        responses={
            200: MessageSerializer,
            404: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
        },
    )
    def get(self, request: Request, message_id: int) -> Response:
        user = cast(User, request.user)

        try:
            message = MessageService.get_message(message_id)
        except Exception:
            raise NotFound("메시지를 찾을 수 없습니다.")

        # 메시지가 속한 그룹의 멤버인지 확인
        try:
            ChatRoomService.validate_member(message.study_group, user)
        except PermissionDenied:
            return Response({"detail": "해당 메시지에 접근 권한이 없습니다."}, status=403)

        return Response(MessageSerializer(message).data)
