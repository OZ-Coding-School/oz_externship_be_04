from typing import Any, Type

from django.db import IntegrityError
from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from apps.recruitment.models import Recruitment, RecruitmentBookmarks
from apps.recruitment.serializers.recruitment_bookmarks import (
    RecruitmentBookmarkCardSerializer,
    RecruitmentBookmarkCreateSerializer,
)


class RecruitmentBookmarkCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-created_at"


class RecruitmentBookmarkListCreateAPIView(APIView):
    pagination_class = RecruitmentBookmarkCursorPagination
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self) -> Type[Serializer[Any]]:
        if self.request.method == "POST":
            return RecruitmentBookmarkCreateSerializer
        return RecruitmentBookmarkCardSerializer

    @extend_schema(
        summary="스터디 구인 공고 북마크 목록 조회",
        description="Cursor Pagination 기반 북마크 목록 조회, 타이틀 검색 가능",
        responses={200: RecruitmentBookmarkCardSerializer},
    )
    def get(self, reqeust: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = self.get_queryset()
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, self.request)
        serializer = RecruitmentBookmarkCardSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def get_queryset(self) -> QuerySet[RecruitmentBookmarks]:
        user = self.request.user
        q = self.request.query_params.get("q")

        if user.is_anonymous:
            return RecruitmentBookmarks.objects.none()

        queryset = RecruitmentBookmarks.objects.select_related("recruitment").filter(user_id=user.id)

        if q:
            queryset = queryset.filter(Q(recruitment__title__icontains=q))
        return queryset

    @extend_schema(
        summary="스터디 구인 공고 북마크 생성",
        request=RecruitmentBookmarkCreateSerializer,
        responses={
            200: OpenApiResponse(description="북마크가 추가되었습니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            404: OpenApiResponse(description="해당 공고를 찾을 수 없습니다."),
            409: OpenApiResponse(description="이미 북마크 한 공고입니다."),
        },
        examples=[
            OpenApiExample(
                "북마크 요청",
                value={"recruitment_uuid": "b8dbd77f-cf73-4ef4-ae15-34e6b6cf1b41"},
            )
        ],
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # if request.user.is_anonymous:
        #     return Response({"detail": "자격 인증 데이터가 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        recruitment_uuid = serializer.validated_data["recruitment_uuid"]
        recruitment = get_object_or_404(Recruitment, uuid=recruitment_uuid)

        user = request.user

        try:
            bookmark, created = RecruitmentBookmarks.objects.get_or_create(
                user_id=user.id,
                recruitment_id=recruitment.id,
            )
        except IntegrityError:
            return Response({"detail": "이미 북마크 한 공고입니다."}, status=status.HTTP_409_CONFLICT)
        if not created:
            return Response({"detail": "이미 북마크 한 공고입니다."}, status=status.HTTP_409_CONFLICT)
        return Response({"detail": "북마크가 추가되었습니다."}, status=status.HTTP_200_OK)


class RecruitmentBookmarkDeleteAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="스터디 구인 공고 북마크 삭제",
        request=RecruitmentBookmarkCreateSerializer,
        responses={
            200: OpenApiResponse(description="북마크가 취소되었습니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
            403: OpenApiResponse(description="권한이 없습니다."),
            404: OpenApiResponse(description="해당 북마크 내역을 찾을 수 없습니다."),
        },
    )
    def delete(self, request: Request) -> Response:
        serializer = RecruitmentBookmarkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recruitment_uuid = serializer.validated_data["recruitment_uuid"]
        recruitment = get_object_or_404(Recruitment, uuid=recruitment_uuid)

        user_id = request.user.id
        if user_id is None:
            return Response({"detail": "자격 인증 데이터가 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        bookmark = RecruitmentBookmarks.objects.filter(
            user_id=user_id,
            recruitment_id=recruitment.id,
        ).first()

        if not bookmark:
            return Response(
                {"detail": "해당 북마크 내역을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        bookmark.delete()
        return Response({"detail": "북마크가 취소되었습니다."}, status=status.HTTP_200_OK)
