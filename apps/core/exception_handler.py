from typing import Any, Type

from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

COMMON_EXCEPTION_MESSAGES: dict[Type[BaseException], tuple[str, int]] = {
    Http404: ("요청한 리소스를 찾을 수 없습니다.", status.HTTP_404_NOT_FOUND),
    exceptions.PermissionDenied: ("권한이 없습니다.", status.HTTP_403_FORBIDDEN),
    exceptions.AuthenticationFailed: ("자격 인증 데이터가 제공되지 않았습니다.", status.HTTP_401_UNAUTHORIZED),
    exceptions.NotAuthenticated: ("인증 정보가 제공되지 않았습니다.", status.HTTP_401_UNAUTHORIZED),
    exceptions.MethodNotAllowed: ("허용되지 않는 메서드입니다.", status.HTTP_405_METHOD_NOT_ALLOWED),
}


def match_common_exception(exc: Exception) -> Response | None:
    for exc_type, (msg, code) in COMMON_EXCEPTION_MESSAGES.items():
        if isinstance(exc, exc_type):
            return Response({"error_detail": msg}, status=code)
    return None


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    error_keys = ["msg", "message", "error", "detail"]

    if common := match_common_exception(exc):
        return common

    if not (response := exception_handler(exc, context)):
        return Response({"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."}, status=500)

    if isinstance(response.data, dict) and (
        matched_key := next((key for key in error_keys if key in response.data), None)
    ):
        response.data = {"error_detail": response.data.pop(matched_key)}
    else:
        response.data = {"error_detail": response.data}

    return response
