from typing import Any, List, cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models import LectureBookmark


class LectureBookmarkIdListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["lecture-bookmark"],
        summary="로그인 유저가 북마크한 강의 ID 목록 조회 API입니다.",
        responses={
            200: OpenApiTypes.OBJECT,
            401: {"example": {"error_detail": "인증 정보가 제공되지 않았습니다."}},
        },
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user_id = cast(int, request.user.id)

        lecture_ids: List[int] = list(
            LectureBookmark.objects.filter(user_id=user_id).values_list("lecture_id", flat=True)
        )

        return Response(
            {"lecture_ids": lecture_ids},
            status=status.HTTP_200_OK,
        )
