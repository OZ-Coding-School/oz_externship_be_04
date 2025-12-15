from django.db.models import Count, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recruitment.models import Recruitment
from apps.recruitment.serializers.recruitment_admin_serializer import (
    AdminRecruitmentDetailSerializer,
    AdminRecruitmentListSerializer,
)

SORT_MAP = {
    "latest": "-created_at",
    "oldest": "created_at",
    "views": "-views_count",
    "bookmarked": "-bookmark_count",
}


def get_admin_recruitment_queryset() -> QuerySet[Recruitment]:
    qs = (
        Recruitment.objects.annotate(
            bookmark_count=Count("recruitment_bookmarks", distinct=True),
            application_count=Count("applications", distinct=True),
        )
        .select_related("study_group", "author")
        .prefetch_related(
            "study_group__studylecture_study_groups__lecture",
            "recruitment_tags__tag",
            "attachments",
            "images",
            "applications__applicant",
        )
    )
    return qs


class AdminRecruitmentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class AdminRecruitmentListView(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = AdminRecruitmentPagination

    @extend_schema(
        operation_id="admin_Recruitment_list",
        summary="Admin 구인 공고 목록 조회",
        tags=["Admin"],
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, required=False, description="구인공고 제목 검색"),
            OpenApiParameter(
                "status",
                OpenApiTypes.STR,
                required=False,
                description="구인 공고 상태 : 'open' (모집중), 'closed' (마감) )",
            ),
            OpenApiParameter(
                "tag",
                OpenApiTypes.STR,
                required=False,
                description="공고 태그별 필터링(단일 태그명 또는 콤마로 구분된 다중 태그)",
            ),
            OpenApiParameter(
                "sort", OpenApiTypes.STR, required=False, description="latest | oldest | views | bookmarked"
            ),
            OpenApiParameter("page", OpenApiTypes.INT, required=False),
            OpenApiParameter("page_size", OpenApiTypes.INT, required=False),
        ],
        responses={200: AdminRecruitmentListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        qs = get_admin_recruitment_queryset()

        # 구인공고 제목 검색
        search_keyword = request.query_params.get("search", "").strip()
        if search_keyword:
            qs = qs.filter(title__icontains=search_keyword)

        # 구인 공고 상태 ( 모집중, 마감 )
        status_param = request.query_params.get("status")
        if status_param == "open":
            qs = qs.filter(is_closed=False)

        elif status_param == "closed":
            qs = qs.filter(is_closed=True)

        # 공고 태그별 필터링(선택된 태그 중 하나라도 포함하는 공고 조회)
        tag_param = request.query_params.get("tag")
        if tag_param:
            tag_names = [t.strip() for t in tag_param.split(",") if t.strip()]
            if tag_names:
                qs = qs.filter(recruitment_tags__tag__name__in=tag_names).distinct()

        # 정렬 기능
        sort_param = request.query_params.get("sort") or "latest"
        order_by_field = SORT_MAP.get(sort_param, SORT_MAP["latest"])
        qs = qs.order_by(order_by_field)

        # 페이지 네이션
        paginator = AdminRecruitmentPagination()
        paginated_qs = paginator.paginate_queryset(qs, request)

        serializer = AdminRecruitmentListSerializer(paginated_qs, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminRecruitmentDetailView(APIView):
    """관리자용 구인공고 상세 조회"""

    permission_classes = [IsAdminUser]

    @extend_schema(
        summary="Admin 구인공고 상세 조회",
        responses={
            200: AdminRecruitmentDetailSerializer,
            403: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "권한이 없습니다."}},
            },
            404: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "해당 공고를 찾을 수 없습니다."}},
            },
        },
        tags=["Admin"],
    )
    def get(self, request: Request, recruitment_id: int) -> Response:
        recruitment = get_admin_recruitment_queryset().filter(id=recruitment_id).first()

        if not recruitment:
            return Response({"error_detail": "해당 구인공고를 찾을 수 없습니다."}, status=404)

        serializer = AdminRecruitmentDetailSerializer(recruitment)
        return Response(serializer.data, status=200)

    @extend_schema(
        tags=["Admin"],
        summary="Admin 구인 공고 삭제",
        responses={
            200: {
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "구인공고가 삭제되었습니다."}},
            },
            403: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "권한이 없습니다."}},
            },
            404: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "해당 공고를 찾을 수 없습니다."}},
            },
        },
    )
    def delete(self, request: Request, recruitment_id: int) -> Response:
        recruitment = get_object_or_404(Recruitment, id=recruitment_id)
        recruitment.delete()
        return Response({"detail": "구인공고가 삭제되었습니다."}, status=status.HTTP_200_OK)
