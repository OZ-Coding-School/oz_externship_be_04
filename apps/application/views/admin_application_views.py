from django.db.models import Q, QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.application.models import Application, ApplicationStatus
from apps.application.serializers.admin_application_serializers import (
    AdminApplicationDetailSerializer,
    AdminApplicationListSerializer,
)

SORT_MAP = {
    "latest": "-created_at",
    "oldest": "created_at",
}


def get_admin_application_queryset() -> QuerySet[Application]:
    return Application.objects.select_related("recruitment", "applicant").prefetch_related(
        "recruitment__study_group__studylecture_set__lecture",
        "recruitment__recruitment_tags__tag",
    )


class AdminApplicationPagination(PageNumberPagination):
    """Admin 전용 페이지네이션"""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class AdminApplicationListView(APIView):
    """[REQ-APLY-009] 관리자용 지원서 목록 조회"""

    permission_classes = [IsAdminUser]
    pagination_class = AdminApplicationPagination

    @extend_schema(
        operation_id="admin_application_list",
        summary="Admin 지원서 목록 조회",
        tags=["Admin"],
        parameters=[
            OpenApiParameter("status", OpenApiTypes.STR, required=False, description="지원 상태 필터"),
            OpenApiParameter("search", OpenApiTypes.STR, required=False, description="통합 검색"),
            OpenApiParameter("sort", OpenApiTypes.STR, required=False, description="latest | oldest"),
            OpenApiParameter("page", OpenApiTypes.INT, required=False),
            OpenApiParameter("page_size", OpenApiTypes.INT, required=False),
        ],
        responses={200: AdminApplicationListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:

        qs = get_admin_application_queryset()

        status_param = request.query_params.get("status")
        if status_param in ApplicationStatus.values:
            qs = qs.filter(status=status_param)

        # 통합 검색 (공고 제목, 지원자 닉네임, 지원자 이메일)
        search_keyword = request.query_params.get("search")
        if search_keyword:
            qs = qs.filter(
                Q(recruitment__title__icontains=search_keyword)
                | Q(applicant__nickname__icontains=search_keyword)
                | Q(applicant__email__icontains=search_keyword)
            )

        sort_param = request.query_params.get("sort") or "latest"
        order_by_field = SORT_MAP.get(sort_param, SORT_MAP["latest"])
        qs = qs.order_by(order_by_field)

        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(qs, request, view=self)

        if paginated_qs is None:
            serializer = AdminApplicationListSerializer(qs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = AdminApplicationListSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminApplicationDetailView(APIView):
    """[REQ-APLY-010] 관리자용 지원서 상세 조회"""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Admin 지원서 상세 조회",
        responses={
            200: AdminApplicationDetailSerializer,
            403: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "권한이 없습니다."}},
            },
            404: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "해당 지원서를 찾을 수 없습니다."}},
            },
        },
        tags=["Admin"],
    )
    def get(self, request: Request, application_id: int) -> Response:

        application = get_admin_application_queryset().filter(id=application_id).first()

        if not application:
            return Response(
                {"error_detail": "해당 지원서를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AdminApplicationDetailSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)
