import random
from decimal import Decimal
from typing import cast

from django.db.models import QuerySet, Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from apps.lectures import models
from apps.lectures.models import CrawledLecture
from apps.lectures.serializers.admin_crawled_lecture_serializer import (
    AdminCrawledLectureRetrieveSerializer,
    AdminCrawledLectureSerializer,
)


class AdminLecturePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class AdminCrawledLectureView(APIView):
    serializer_class = AdminCrawledLectureSerializer
    permission_classes = [IsAdminUser]
    pagination_class = AdminLecturePagination

    @extend_schema(
        operation_id="v1_admin_crawled_lectures_list",
        tags=["lectures"],
        summary="크롤링한 강의 목록 (관리자)",
        parameters=[
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location="query",
                description="원하는 페이지 번호를 입력하여 해당하는 페이지의 강의 내용을 가져올 수 있습니다.",
                required=False,
            ),
            OpenApiParameter(
                name="page_size",
                type=OpenApiTypes.INT,
                location="query",
                description="한 페이지에 몇 개의 결과를 보여줄지 지정 할 수 있습니다.",
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
            200: AdminCrawledLectureSerializer(many=True),
            401: {"example": {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."}},
            403: {
                "example": {"error_detail": "권한이 없습니다."},
            },
        },
    )
    def get(self, request: Request) -> Response:
        search: str | None = request.query_params.get("search")
        queryset = CrawledLecture.objects.all().order_by("-created_at")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(instrector__icontains=search)
            )

        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(queryset, request)

        serializer = self.serializer_class(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminCrawledLectureRetrieveView(APIView):
    serializer_class = AdminCrawledLectureRetrieveSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        operation_id="v1_admin_crawled_lecture_detail",
        tags=["lectures"],
        summary="크롤링한 강의 상세 조회 (관리자)",
        responses={
            200: AdminCrawledLectureRetrieveSerializer(),
            401: {"example": {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."}},
            403: {"example": {"error_detail": "권한이 없습니다."}},
            404: {"example": {"error_detail": "강의 정보를 찾을 수 없습니다."}},
        },
    )
    def get(self, request: Request, lecture_id: int) -> Response:
        lecture = get_object_or_404(CrawledLecture, id=lecture_id)
        serializer = self.serializer_class(lecture)

        return Response(serializer.data, status=status.HTTP_200_OK)
