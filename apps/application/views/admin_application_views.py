from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.application.models import Application
from apps.application.serializers.admin_application_serializers import (
    AdminApplicationDetailSerializer,
    AdminApplicationListSerializer,
)

SORT_MAP = {
    "latest": "-created_at",
    "oldest": "created_at",
}


def safe_int(value: str | None, default: int) -> int:
    """문자열 숫자를 정수로 변환"""
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


class AdminApplicationListView(APIView):
    """[REQ-APLY-009] 관리자용 지원서 목록 조회"""

    permission_classes = [IsAdminUser]

    @extend_schema(
        operation_id="admin_application_list",
        summary="Admin 지원서 목록 조회",
        tags=["Application - Admin"],
        parameters=[
            OpenApiParameter("status", OpenApiTypes.STR, required=False, description="지원 상태 필터"),
            OpenApiParameter("recruitment_title", OpenApiTypes.STR, required=False, description="공고 제목 검색"),
            OpenApiParameter("applicant_nickname", OpenApiTypes.STR, required=False, description="지원자 닉네임 검색"),
            OpenApiParameter("sort", OpenApiTypes.STR, required=False, description="latest | oldest"),
            OpenApiParameter("page", OpenApiTypes.INT, required=False),
            OpenApiParameter("size", OpenApiTypes.INT, required=False),
        ],
        responses={200: AdminApplicationListSerializer},
    )
    def get(self, request: Request) -> Response:

        qs = Application.objects.select_related("recruitment", "applicant").prefetch_related(
            "recruitment__study_group__studylecture_set__lecture_id",
            "recruitment__recruitment_tags__tag",
        )

        # 지원 상태 필터링
        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        # 공고 제목 검색
        recruitment_title = request.query_params.get("recruitment_title")
        if recruitment_title:
            qs = qs.filter(recruitment__title__icontains=recruitment_title)

        # 지원자 닉네임 검색
        applicant_nickname = request.query_params.get("applicant_nickname")
        if applicant_nickname:
            qs = qs.filter(applicant__nickname__icontains=applicant_nickname)

        # 정렬
        sort = request.query_params.get("sort", "latest")
        qs = qs.order_by(SORT_MAP.get(sort, "-created_at"))

        # TODO: 페이지네이션(현재 전체 리스트 반환)
        page = safe_int(request.query_params.get("page"), 1)
        size = safe_int(request.query_params.get("size"), 10)

        total_count = qs.count()

        serializer = AdminApplicationListSerializer(qs, many=True)

        return Response(
            {
                "count": total_count,
                "page": page,
                "size": size,
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class AdminApplicationDetailView(APIView):
    """[REQ-APLY-010] 관리자용 지원서 상세 조회"""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Admin 지원서 상세 조회",
        responses={200: AdminApplicationDetailSerializer},
        tags=["Application - Admin"],
    )
    def get(self, request: Request, application_uuid: str) -> Response:

        application = (
            Application.objects.select_related("recruitment", "applicant")
            .prefetch_related(
                "recruitment__study_group__studylecture_set__lecture_id",
                "recruitment__recruitment_tags__tag",
            )
            .filter(uuid=application_uuid)
            .first()
        )

        if not application:
            return Response(
                {"error_detail": "해당 지원서를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AdminApplicationDetailSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)
