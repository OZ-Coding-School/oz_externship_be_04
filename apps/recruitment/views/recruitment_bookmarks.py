from typing import Any

from django.db.models import Count, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recruitment.models import Recruitment, RecruitmentBookmarks
from apps.recruitment.serializers.recruitment_bookmarks import (
    RecruitmentBookmarkCardSerializer,
    RecruitmentBookmarkCreateSerializer,
)


class RecruitmentBookmarkCursorPagination(CursorPagination):
    """북마크 목록용 커서 페이지네이션"""

    page_size = 10
    ordering = "-created_at"


class RecruitmentBookmarkListCreateAPIView(APIView):
    """북마크 목록 조회 및 생성 API"""

    permission_classes = [IsAuthenticated]
    pagination_class = RecruitmentBookmarkCursorPagination

    @extend_schema(
        summary="북마크 목록 조회",
        description="사용자의 북마크 목록을 조회합니다. Cursor Pagination 기반이며, 제목 검색을 지원합니다.",
        parameters=[
            {
                "name": "q",
                "in": "query",
                "description": "공고 제목 검색어",
                "required": False,
                "schema": {"type": "string"},
            }
        ],
        responses={200: RecruitmentBookmarkCardSerializer(many=True), 401: OpenApiResponse(description="인증 필요")},
    )
    def get(self, request: Request) -> Response:
        """북마크 목록 조회"""
        queryset = self.get_queryset(request)
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = RecruitmentBookmarkCardSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="북마크 추가",
        description="공고를 북마크에 추가합니다.",
        request=RecruitmentBookmarkCreateSerializer,
        responses={
            201: OpenApiResponse(description="북마크가 추가되었습니다."),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증 필요"),
            404: OpenApiResponse(description="공고를 찾을 수 없습니다."),
            409: OpenApiResponse(description="이미 북마크한 공고입니다."),
        },
        examples=[
            OpenApiExample(
                "북마크 요청 예시",
                value={"recruitment_uuid": "b8dbd77f-cf73-4ef4-ae15-34e6b6cf1b41"},
            )
        ],
    )
    def post(self, request: Request) -> Response:
        """북마크 추가"""
        serializer = RecruitmentBookmarkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recruitment_uuid = serializer.validated_data["recruitment_uuid"]
        recruitment = get_object_or_404(Recruitment, uuid=recruitment_uuid)

        bookmark, created = RecruitmentBookmarks.objects.get_or_create(
            user_id=request.user,
            recruitment_id=recruitment,
        )

        if not created:
            return Response({"error_detail": "이미 북마크한 공고입니다."}, status=status.HTTP_409_CONFLICT)

        return Response({"detail": "북마크가 추가되었습니다."}, status=status.HTTP_201_CREATED)

    def get_queryset(self, request: Request) -> QuerySet[RecruitmentBookmarks]:
        """북마크 쿼리셋 반환 (검색 및 최적화 포함)"""
        queryset = (
            RecruitmentBookmarks.objects.filter(user_id=request.user)
            .select_related("recruitment_id__study_group", "recruitment_id__author")
            .prefetch_related(
                "recruitment_id__images",
                "recruitment_id__recruitment_tags__tag",
                "recruitment_id__study_group__studylecture_set__lecture",
            )
            .annotate(bookmark_count=Count("recruitment_id__recruitment_bookmarks"))
        )

        search_query = request.query_params.get("q")
        if search_query:
            queryset = queryset.filter(recruitment_id__title__icontains=search_query)

        return queryset


class RecruitmentBookmarkDeleteAPIView(APIView):
    """북마크 삭제 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="북마크 삭제",
        description="북마크를 삭제합니다.",
        request=RecruitmentBookmarkCreateSerializer,
        responses={
            200: OpenApiResponse(description="북마크가 삭제되었습니다."),
            400: OpenApiResponse(description="잘못된 요청"),
            401: OpenApiResponse(description="인증 필요"),
            404: OpenApiResponse(description="북마크를 찾을 수 없습니다."),
        },
        examples=[
            OpenApiExample(
                "북마크 삭제 요청 예시",
                value={"recruitment_uuid": "b8dbd77f-cf73-4ef4-ae15-34e6b6cf1b41"},
            )
        ],
    )
    def delete(self, request: Request) -> Response:
        """북마크 삭제"""
        serializer = RecruitmentBookmarkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recruitment_uuid = serializer.validated_data["recruitment_uuid"]
        recruitment = get_object_or_404(Recruitment, uuid=recruitment_uuid)

        bookmark = RecruitmentBookmarks.objects.filter(
            user_id=request.user,
            recruitment_id=recruitment,
        ).first()

        if not bookmark:
            return Response(
                {"error_detail": "해당 북마크를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        bookmark.delete()

        return Response({"detail": "북마크가 삭제되었습니다."}, status=status.HTTP_200_OK)
