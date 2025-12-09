from typing import List

from django.conf import settings
from django.db.models import Q, QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import (
    Pageable,
    offset_paginate_list,
    offset_paginate_queryset,
)
from apps.lectures.models import CrawledLecture, LectureBookmark
from apps.lectures.serializers.lecture_bookmark_serializer import (
    LectureBookmarkListSerializer,
    LectureBookmarkSerializer,
)


class LectureBookmarkListCreateAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = LectureBookmarkSerializer
    list_serializer_class = LectureBookmarkListSerializer
    search_fields = ["lecture__title", "lecture__instructor"]

    def get_queryset(self) -> QuerySet[LectureBookmark]:
        qs = LectureBookmark.objects.select_related("lecture").all()

        if search := self.request.GET.get("search"):
            q = Q()
            for field in self.search_fields:
                q |= Q(**{f"{field}__icontains": search})
            qs = qs.filter(q)

        return qs

    @staticmethod
    def _parse_pageable(request: Request) -> Pageable:
        cursor_param = request.query_params.get("cursor")
        page_size_param = request.query_params.get("page_size")

        try:
            page = int(cursor_param) if cursor_param is not None else 1
        except (TypeError, ValueError):
            page = 1

        try:
            size = int(page_size_param) if page_size_param is not None else 10
        except (TypeError, ValueError):
            size = 10

        return Pageable(page=page, size=size)

    def _get_mock_bookmarks(self) -> List[LectureBookmark]:
        mock_lectures: List[CrawledLecture] = []
        for i in range(1, 21):
            lecture = CrawledLecture(
                id=i,
                title=f"북마크 Mock 강의 {i}",
                instructor=f"북마크 강사 {i}",
                total_class_time=3600 * i,
                original_price=10000 * i,
                discount_price=8000 * i,
                difficulty=CrawledLecture.DifficultyEnum.EASY,
                thumbnail_img_url="https://example.com/mock_thumbnail.jpg",
                platform=CrawledLecture.PlatformEnum.INFLEARN,
                url_link=f"https://example.com/mock_lecture_{i}",
            )
            mock_lectures.append(lecture)

        mock_bookmarks: List[LectureBookmark] = [
            LectureBookmark(user_id=1, lecture=lecture) for lecture in mock_lectures
        ]

        if search := self.request.GET.get("search"):
            lowered = search.lower()
            mock_bookmarks = [
                bm
                for bm in mock_bookmarks
                if lowered in (bm.lecture.title or "").lower() or lowered in (bm.lecture.instructor or "").lower()
            ]

        return mock_bookmarks

    @extend_schema(
        tags=["lecture-bookmark"],
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
        pageable = self._parse_pageable(request)

        if settings.DEBUG:
            bookmarks = self._get_mock_bookmarks()
            page = offset_paginate_list(bookmarks, pageable)
        else:
            queryset = self.get_queryset()
            page = offset_paginate_queryset(queryset, pageable)

        serializer = self.list_serializer_class(page.items, many=True)

        base_url = request.build_absolute_uri(request.path)

        def build_page_url(page_number: int) -> str:
            query_params = request.query_params.copy()
            query_params["cursor"] = str(page_number)
            query_params["page_size"] = str(pageable.size)
            return f"{base_url}?{query_params.urlencode()}"

        next_url = build_page_url(page.current_page + 1) if page.has_next else None
        prev_url = build_page_url(page.current_page - 1) if page.has_prev else None

        return Response(
            {
                "next": next_url,
                "previous": prev_url,
                "results": serializer.data,
            }
        )

    @extend_schema(
        tags=["lecture-bookmark"],
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

        return Response(
            {"detail": "북마크를 추가하였습니다."},
            status=201,
        )


class LectureBookmarkDestroyAPIView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["lecture-bookmark"],
        summary="강의 북마크를 삭제하는 API입니다.",
        responses={
            200: {"example": {"detail": "북마크를 취소하였습니다."}},
            404: {"example": {"error_detail": "북마크 정보를 찾을 수 없습니다."}},
        },
    )
    def delete(self, request: Request, lecture_id: int) -> Response:
        return Response(
            {"detail": "북마크를 취소하였습니다."},
            status=200,
        )
