from typing import Optional, cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.notification.models import Notification
from apps.users.models import User


# 전제 알림 읽음 처리
class NotificationReadAllViews(APIView):
    permission_classes = [AllowAny] # 유저 구현되기 전 AllowAny로 지정

    @extend_schema(
        tags = ["notification"],
        summary="로그인 유저가 수신한 알림중 읽지 않은 모든 알림을 읽음 처리하는 API 입니다.",
        responses ={
            200: {
                "type": "object",
                  "example": {"detail": "모든 알림 읽음처리에 성공하였습니다."}
            },
            401: {
                "type": "object",
                "example": {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."}
            },
        },
    )
    #
    def post(self, request: Request) -> Response:
        user = cast(User, request.user)
        Notification.objects.filter(user=user, is_read=False).update(is_read=True)
        return Response({"detail": "알림 읽음처리에 성공하였습니다."}, status=status.HTTP_200_OK)

# 단건 알림 조회
class NotificationReadView(APIView):
    permission_classes = [AllowAny] # 유저 구현되기 전 AllowAny로 지정

    @extend_schema(
        tags = ["notification"],
        summary="로그인 유저가 수신한 특정 알림을 읽음 처리하는 API 입니다.",
        responses ={
            200: {
                "type": "object",
                "example": {"detail": "알림 읽음처리에 성공하였습니다."}
            },
            401: {
                "type": "object",
                "example": {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."}
            },
            403: {
                "type": "object",
                "example": {"error_detail": "권한이 없습니다."}
            },
            404: {
                "type": "object",
                "example": {"error_detail": "해당 알림 내역을 찾을 수 없습니다."}
            },
        },
    )

    def post(self, request: Request, notification_id: int) -> Response:
        notification = self.get_object(notification_id)
        if not notification:
            return Response({"error": "해당 알림 내역을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, notification)
        notification.is_read = True
        notification.save(update_fields=["is_read"])

        return Response({"detail": "알림 읽음처리에 성공하였습니다."}, status=status.HTTP_200_OK)

    def get_object(self, notification_id: int) -> Optional[Notification]:
        try:
            return Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            return None
