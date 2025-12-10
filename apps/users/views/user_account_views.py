from typing import Any

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.withdrawal_serializers import WithdrawalSerializer
from apps.users.services.withdrawal_services import withdraw_service


class UserAccountView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request: Any, *args: Any, **kwargs: Any) -> Response:
        serializer = WithdrawalSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({"error_detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        data.pop("agree_check")

        withdraw_service(request.user, data)
        return Response(
            {
                "detail": "회원 탈퇴 처리가 완료되었습니다. 14일 후 계정이 영구 삭제되며, 그전에 다시 로그인하시면 계정을 복구하실 수 있습니다."
            },
            status=status.HTTP_200_OK,
        )
