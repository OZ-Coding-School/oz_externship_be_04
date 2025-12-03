from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recruitment.models import Recruitment, RecruitmentBookmarks
from apps.recruitment.serializers.recruitment_bookmarks import (
    RecruitmentBookmarkCardSerializer,
    RecruitmentBookmarkCreateSerializer,
)


class RecruitmentBookmarkCursorPagination(CursorPagination):
    page_size = 10
    ordering = "-created_at"


class RecruitmentBookmarkListAPIView(generics.ListAPIView):
    serializer_class = RecruitmentBookmarkCardSerializer
    pagination_class = RecruitmentBookmarkCursorPagination
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="스터디 구인 공고 북마크 목록 조회",
        description="Cursor Pagination 기반 북마크 목록 조회, 제목 검색 가능",
        responses={200: RecruitmentBookmarkCardSerializer},
        parameters=[],
    )
    def get_queryset(self):
        user = self.request.user
        q = self.request.query_params.get("q")

        queryset = RecruitmentBookmarks.objects.select_related("user", "recruitment").filter(user_id=user.id)

        if q:
            queryset = queryset.filter(Q(recruitment__title__icontains=q))

        return queryset


class RecruitmentBookmarkCreateAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="스터디 구인 공고 북마크 생성",
        request=RecruitmentBookmarkCreateSerializer,
        responses={
            201: OpenApiResponse(description="북마크가 추가되었습니다."),
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
    def post(self, request):
        serializer = RecruitmentBookmarkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recruitment_uuid = serializer.validated_data["recruitment_uuid"]
        recruitment = get_object_or_404(Recruitment, uuid=recruitment_uuid)

        user = request.user

        exists = RecruitmentBookmarks.objects.filter(user_id=user.id, recruitment_id=recruitment.id).exists()

        if exists:
            return Response(
                {"detail": "이미 북마크한 공고입니다."},
                status=status.HTTP_409_CONFLICT,
            )

        RecruitmentBookmarks.objects.create(
            user_id=user.id,
            recruitment_id=recruitment.id,
        )

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
            404: OpenApiResponse(description="해당 북마크 내역을 찾을 수 없습니다.")
        },
    )
    def delete(self, request):
        serializer = RecruitmentBookmarkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recruitment_uuid = serializer.validated_data["recruitment_uuid"]
        recruitment = get_object_or_404(Recruitment, uuid=recruitment_uuid)

        bookmark = RecruitmentBookmarks.objects.filter(
            user_id=request.user.id,
            recruitment_id=recruitment.id,
        ).first()

        if not bookmark:
            return Response(
                {"detail": "해당 북마크 내역을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        bookmark.delete()
        return Response({"detail": "북마크가 취소되었습니다."}, status=status.HTTP_200_OK)
