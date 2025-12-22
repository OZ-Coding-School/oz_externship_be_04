from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_groups.models import StudyGroup
from apps.study_groups.serializers import (  # AdminStudyGroupDetailSerializer,
    AdminStudyGroupListSerializer,
)
from apps.study_groups.services.admin_study_group_services import (
    filter_study_groups_by_name,
    filter_study_groups_by_status,
    get_admin_study_group_queryset,
)


# 스터디 그룹 페이지네이션 (PageNumberPagination)
class AdminStudyGroupPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 100


# 그룹 목록
class AdminStudyGroupListView(APIView):
    permission_classes = [IsAdminUser]
    pagination_class = AdminStudyGroupPagination

    @extend_schema(
        operation_id="admin_study_group_list",
        summary="Admin 스터디 그룹 목록 조회",
        tags=["Admin"],
        parameters=[
            OpenApiParameter(
                "search",
                OpenApiTypes.STR,
                required=False,
                description="그룹명 검색",
            ),
            OpenApiParameter(
                "status",
                OpenApiTypes.STR,
                required=False,
                description="스터디 상태 필터",
                enum=["PENDING", "ONGOING", "ENDED"],
            ),
            OpenApiParameter("page", OpenApiTypes.INT, required=False),
            OpenApiParameter("page_size", OpenApiTypes.INT, required=False),
        ],
        responses={200: AdminStudyGroupListSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        qs = get_admin_study_group_queryset()

        # 그룹명 검색
        search = request.query_params.get("search")
        qs = filter_study_groups_by_name(qs, search)

        # 스터디 상태 검색
        status_param = request.query_params.get("status")
        if status_param and status_param in [choice[0] for choice in StudyGroup.StudyGroupStatusChoices.choices]:
            qs = filter_study_groups_by_status(qs, status_param)

        paginator = self.pagination_class()
        paginated_qs = paginator.paginate_queryset(qs, request, view=self)

        if paginated_qs is None:
            serializer = AdminStudyGroupListSerializer(qs, many=True, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = AdminStudyGroupListSerializer(paginated_qs, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
