from typing import Any, Sequence, cast

from django.db.models import Q, QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models import CrawledLecture, LectureBookmark
from apps.lectures.serializers.lecture_bookmark_serializer import (
    LectureBookmarkListSerializer,
    LectureBookmarkSerializer,
)


class LectureBookmarkPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
    page_query_param = "cursor"

    def get_paginated_response(self, data: Any) -> Response:
        return Response(
            {
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )


class LectureBookmarkListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LectureBookmarkSerializer
    list_serializer_class = LectureBookmarkListSerializer
    search_fields = ["lecture__title", "lecture__instructor"]
    pagination_class: type[LectureBookmarkPagination] = LectureBookmarkPagination

    def _get_user_id(self) -> int:
        user_id = self.request.user.id
        assert isinstance(user_id, int)
        return user_id

    def get_queryset(self) -> QuerySet[LectureBookmark]:
        qs = LectureBookmark.objects.select_related("lecture").filter(
            user_id=self._get_user_id(),
        )

        if search := self.request.query_params.get("search"):
            q = Q()
            for field in self.search_fields:
                q |= Q(**{f"{field}__icontains": search})
            qs = qs.filter(q)

        return qs

    @extend_schema(
        tags=["Lecture"],
        summary="강의 북마크 목록을 조회하는 API입니다.",
        parameters=[
            OpenApiParameter(
                name="cursor",
                type=OpenApiTypes.INT,
                location="query",
                description="현재 페이지 번호입니다. (기본값: 1)",
                required=False,
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location="query",
                description="한 페이지에 포함될 북마크 강의 개수입니다. (기본값: 10)",
                required=False,
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location="query",
                description="강의 제목 또는 강사 이름으로 검색합니다.",
                required=False,
            ),
        ],
        responses={
            200: LectureBookmarkListSerializer(many=True, read_only=True),
            500: {"example": {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."}},
        },
    )
    def get(self, request: Request) -> Response:
        paginator: LectureBookmarkPagination = self.pagination_class()

        queryset = self.get_queryset()
        page = cast(
            Sequence[LectureBookmark],
            paginator.paginate_queryset(queryset, request),
        )

        serializer = self.list_serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["Lecture"],
        summary="강의 북마크를 등록/취소하는 API입니다.",
        request=LectureBookmarkSerializer,
        responses={
            201: {"example": {"detail": "북마크를 추가하였습니다."}},
            200: {"example": {"detail": "북마크를 취소하였습니다."}},
            400: {"example": {"error_detail": {"lecture": ["이 필드는 필수 항목입니다."]}}},
        },
    )
    def post(self, request: Request) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        lecture = serializer.validated_data["lecture"]
        assert isinstance(lecture, CrawledLecture)

        user_id = request.user.id
        assert isinstance(user_id, int)

        bookmark, created = LectureBookmark.objects.get_or_create(
            user_id=user_id,
            lecture=lecture,
        )

        if not created:
            bookmark.delete()
            return Response(
                {"detail": "북마크를 취소하였습니다."},
                status=200,
            )

        return Response(
            {"detail": "북마크를 추가하였습니다."},
            status=201,
        )


class LectureBookmarkDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Lecture"],
        summary="강의 북마크를 삭제하는 API입니다.",
        responses={
            200: {"example": {"detail": "북마크를 취소하였습니다."}},
            401: {"example": {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."}},
            404: {"example": {"error_detail": "북마크 정보를 찾을 수 없습니다."}},
            500: {"example": {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."}},
        },
    )
    def delete(self, request: Request, lecture_id: int) -> Response:
        user_id = request.user.id
        assert isinstance(user_id, int)

        bookmark = LectureBookmark.objects.filter(
            lecture_id=lecture_id,
            user_id=user_id,
        ).first()

        if bookmark is None:
            return Response(
                {"error_detail": "북마크 정보를 찾을 수 없습니다."},
                status=404,
            )

        bookmark.delete()

        return Response(
            {"detail": "북마크를 취소하였습니다."},
            status=200,
        )
