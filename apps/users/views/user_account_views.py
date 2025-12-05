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
            error_key = next(iter(serializer.errors))
            error_call = serializer.errors[error_key][0]
            return Response({"error_detail": error_call}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        data.pop("agree_check")

        withdraw_service(request.user, data)
        return Response({}, status=status.HTTP_204_NO_CONTENT)
