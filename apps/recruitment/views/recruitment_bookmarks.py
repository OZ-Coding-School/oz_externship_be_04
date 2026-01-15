from __future__ import annotations

from typing import Optional

from django.db import transaction
from django.db.models import Count, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
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
from apps.users.models import User

ERROR_MESSAGES = {
    "RECRUITMENT_NOT_FOUND": "해당 공고를 찾을 수 없습니다.",
    "BOOKMARK_NOT_FOUND": "해당 북마크 내역을 찾을 수 없습니다.",
    "BOOKMARK_ALREADY_EXISTS": "이미 북마크한 공고입니다.",
    "PERMISSION_DENIED": "권한이 없습니다.",
    "UNAUTHENTICATED": "자격 인증 데이터가 제공되지 않았습니다.",
}

SUCCESS_MESSAGES = {
    "BOOKMARK_CREATED": "북마크가 추가되었습니다.",
    "BOOKMARK_DELETED": "북마크가 취소되었습니다.",
}

RESPONSE_SCHEMAS = {
    "401_UNAUTHORIZED": {
        "type": "object",
        "properties": {"error_detail": {"type": "string", "example": "자격 인증 데이터가 제공되지 않았습니다."}},
    },
    "403_FORBIDDEN": {
        "type": "object",
        "properties": {"error_detail": {"type": "string", "example": "권한이 없습니다."}},
    },
    "404_NOT_FOUND": {
        "type": "object",
        "properties": {"error_detail": {"type": "string", "example": "해당 공고를 찾을 수 없습니다."}},
    },
    "404_BOOKMARK_NOT_FOUND": {
        "type": "object",
        "properties": {"error_detail": {"type": "string", "example": "해당 북마크 내역을 찾을 수 없습니다."}},
    },
    "409_CONFLICT": {
        "type": "object",
        "properties": {"error_detail": {"type": "string", "example": "이미 북마크한 공고입니다."}},
    },
}


class RecruitmentBookmarkCursorPagination(CursorPagination):
    """북마크 목록용 커서 페이지네이션"""

    page_size = 10
    page_size_query_param = "page_size"
    ordering = "-created_at"


def error_response(message: str, status_code: int) -> Response:
    """에러 응답 생성"""
    return Response({"error_detail": message}, status=status_code)


def success_response(message: str, status_code: int = status.HTTP_200_OK) -> Response:
    """성공 응답 생성"""
    return Response({"detail": message}, status=status_code)


def get_authenticated_user(request: Request) -> User:
    """인증된 사용자 객체 반환"""
    user = request.user
    assert isinstance(user, User)
    return user


def get_bookmark_queryset(user: User, search: Optional[str] = None) -> QuerySet[RecruitmentBookmarks]:
    """
    북마크 QuerySet 생성 (최적화된 쿼리)

    Args:
        user: 사용자 객체
        search: 검색어 (공고 제목)

    Returns:
        최적화된 북마크 QuerySet
    """
    queryset = (
        RecruitmentBookmarks.objects.filter(user_id_id=user.id)
        .select_related("recruitment_id__study_group", "recruitment_id__author")
        .prefetch_related(
            "recruitment_id__images",
            "recruitment_id__recruitment_tags__tag",
            "recruitment_id__study_group__studylecture_study_groups__lecture",
        )
        .annotate(bookmark_count=Count("recruitment_id__recruitment_bookmarks"))
    )

    if search:
        queryset = queryset.filter(recruitment_id__title__icontains=search)

    return queryset


def validate_bookmark_permission(bookmark_id: int, user: User) -> tuple[RecruitmentBookmarks | None, Response | None]:
    """
    북마크 접근 권한 검증

    Args:
        bookmark_id: 북마크 ID
        user: 사용자 객체

    Returns:
        (북마크 객체, 에러 응답) 튜플
        성공 시: (bookmark, None)
        실패 시: (None, error_response)
    """
    bookmark = RecruitmentBookmarks.objects.filter(id=bookmark_id).select_related("user_id").first()

    if bookmark is None:
        return None, error_response(ERROR_MESSAGES["BOOKMARK_NOT_FOUND"], status.HTTP_404_NOT_FOUND)

    if bookmark.user_id != user:
        return None, error_response(ERROR_MESSAGES["PERMISSION_DENIED"], status.HTTP_403_FORBIDDEN)

    return bookmark, None


class RecruitmentBookmarkListCreateView(APIView):
    """북마크 목록 조회 및 추가 API"""

    permission_classes = [IsAuthenticated]
    pagination_class = RecruitmentBookmarkCursorPagination

    @extend_schema(
        summary="북마크 목록 조회",
        description="사용자의 북마크 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(name="cursor", type=str, description="커서 값"),
            OpenApiParameter(name="page_size", type=int, description="페이지 크기 (기본 10)"),
            OpenApiParameter(name="search", type=str, description="공고 제목 검색"),
        ],
        responses={
            200: RecruitmentBookmarkCardSerializer(many=True),
            401: RESPONSE_SCHEMAS["401_UNAUTHORIZED"],
        },
        tags=["Recruitment"],
    )
    def get(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        search = request.query_params.get("search")
        queryset = get_bookmark_queryset(user, search)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer = RecruitmentBookmarkCardSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = RecruitmentBookmarkCardSerializer(queryset, many=True)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="북마크 추가",
        description="공고를 북마크에 추가합니다.",
        request=RecruitmentBookmarkCreateSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "북마크가 추가되었습니다."}},
            },
            401: RESPONSE_SCHEMAS["401_UNAUTHORIZED"],
            404: RESPONSE_SCHEMAS["404_NOT_FOUND"],
            409: RESPONSE_SCHEMAS["409_CONFLICT"],
        },
        tags=["Recruitment"],
    )
    @transaction.atomic
    def post(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        serializer = RecruitmentBookmarkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recruitment_uuid = serializer.validated_data["recruitment_uuid"]
        recruitment = get_object_or_404(Recruitment, uuid=recruitment_uuid)

        bookmark, created = RecruitmentBookmarks.objects.get_or_create(
            user_id=user,
            recruitment_id=recruitment,
        )

        if not created:
            return error_response(ERROR_MESSAGES["BOOKMARK_ALREADY_EXISTS"], status.HTTP_409_CONFLICT)

        return success_response(SUCCESS_MESSAGES["BOOKMARK_CREATED"])


class RecruitmentBookmarkDeleteView(APIView):
    """북마크 삭제 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="북마크 삭제",
        description="북마크를 삭제합니다.",
        responses={
            200: {
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "북마크가 취소되었습니다."}},
            },
            401: RESPONSE_SCHEMAS["401_UNAUTHORIZED"],
            403: RESPONSE_SCHEMAS["403_FORBIDDEN"],
            404: RESPONSE_SCHEMAS["404_BOOKMARK_NOT_FOUND"],
        },
        tags=["Recruitment"],
    )
    @transaction.atomic
    def delete(self, request: Request, bookmark_id: int) -> Response:
        user = get_authenticated_user(request)
        bookmark, error = validate_bookmark_permission(bookmark_id, user)
        if error:
            return error
        assert bookmark is not None

        bookmark.delete()

        return success_response(SUCCESS_MESSAGES["BOOKMARK_DELETED"])
