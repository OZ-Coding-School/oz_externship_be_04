from typing import Any, List, cast
from uuid import UUID

from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import OffsetPage, Pageable, offset_paginate_queryset
from apps.recruitment.serializers import (
    RecruitmentCreateSerializer,
    RecruitmentDetailSerializer,
    RecruitmentListSerializer,
    RecruitmentUpdateSerializer,
)
from apps.recruitment.services import RecruitmentService
from apps.users.models import User

SUCCESS_MESSAGES = {
    "RECRUITMENT_CREATED": "공고가 작성되었습니다.",
    "RECRUITMENT_DELETED": "공고가 삭제되었습니다.",
}

RESPONSE_SCHEMAS = {
    "400_BAD_REQUEST": {
        "type": "object",
        "properties": {"error_detail": {"type": "string", "example": "페이지 값이 유효하지 않습니다."}},
    },
    "400_VALIDATION_ERROR": {
        "type": "object",
        "properties": {
            "error_detail": {
                "type": "object",
                "example": {"content": ["내용은 공백일 수 없습니다."]},
            }
        },
    },
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
    "404_PAGE_NOT_FOUND": {
        "type": "object",
        "properties": {"error_detail": {"type": "string", "example": "요청한 페이지를 찾을 수 없습니다."}},
    },
}


def build_paginated_response(request: Request, page: OffsetPage[Any], serializer_data: List[Any]) -> dict[str, Any]:
    """
    페이지네이션 응답 데이터 구성

    Args:
        request: HTTP request 객체
        page: Page 객체
        serializer_data: 직렬화된 데이터 (list)

    Returns:
        페이지네이션 응답 dict
    """
    base_url = request.build_absolute_uri(request.path)
    query_params = request.query_params.copy()

    next_url = None
    if page.has_next:
        query_params["page"] = str(page.current_page + 1)
        next_url = f"{base_url}?{query_params.urlencode()}"

    previous_url = None
    if page.has_prev:
        query_params["page"] = str(page.current_page - 1)
        previous_url = f"{base_url}?{query_params.urlencode()}"

    return {
        "count": page.total_count,
        "next": next_url,
        "previous": previous_url,
        "results": serializer_data,
    }


class RecruitmentListCreateView(APIView):
    """공고 목록 조회 및 작성 API"""

    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="공고 목록 조회",
        description="전체 모집 공고 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(name="page", type=int, description="페이지 번호"),
            OpenApiParameter(name="page_size", type=int, description="페이지 크기"),
            OpenApiParameter(name="search", type=str, description="검색 키워드"),
            OpenApiParameter(
                name="sort",
                type=str,
                description="정렬",
                enum=["latest", "oldest", "most_views", "most_bookmarks"],
            ),
            OpenApiParameter(name="tags", type=str, description="태그 (쉼표 구분)"),
            OpenApiParameter(name="is_closed", type=bool, description="마감 여부"),
        ],
        responses={
            200: RecruitmentListSerializer(many=True),
            400: RESPONSE_SCHEMAS["400_BAD_REQUEST"],
            404: RESPONSE_SCHEMAS["404_PAGE_NOT_FOUND"],
        },
        tags=["Recruitment"],
    )
    def get(self, request: Request) -> Response:
        queryset = RecruitmentService.get_filtered_recruitments(
            base_filter=Q(),
            search=request.query_params.get("search"),
            tags=request.query_params.get("tags"),
            is_closed=request.query_params.get("is_closed"),
            sort=request.query_params.get("sort", "latest"),
            allow_oldest=True,
        )

        pageable = Pageable.from_params(request.query_params.get("page"), request.query_params.get("page_size"))
        page = offset_paginate_queryset(queryset, pageable)

        serializer = RecruitmentListSerializer(page.items, many=True)
        response_data = build_paginated_response(request, page, list(serializer.data))

        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="공고 작성",
        description="스터디 모집 공고를 작성합니다.",
        request=RecruitmentCreateSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "공고가 작성되었습니다."}},
            },
            400: RESPONSE_SCHEMAS["400_VALIDATION_ERROR"],
            401: RESPONSE_SCHEMAS["401_UNAUTHORIZED"],
            403: RESPONSE_SCHEMAS["403_FORBIDDEN"],
            404: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "스터디 그룹을 찾을 수 없습니다."}},
            },
        },
        tags=["Recruitment"],
    )
    def post(self, request: Request) -> Response:
        serializer = RecruitmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = cast(User, request.user)
        RecruitmentService.create_recruitment(user=user, validated_data=serializer.validated_data)

        return Response({"detail": SUCCESS_MESSAGES["RECRUITMENT_CREATED"]}, status=status.HTTP_200_OK)


class RecruitmentMineView(APIView):
    """내가 작성한 공고 목록 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내가 작성한 공고 목록",
        description="사용자가 작성한 공고 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(name="page", type=int, description="페이지 번호"),
            OpenApiParameter(name="page_size", type=int, description="페이지 크기"),
            OpenApiParameter(name="search", type=str, description="검색 키워드"),
            OpenApiParameter(
                name="sort",
                type=str,
                description="정렬 (oldest 제외)",
                enum=["latest", "most_views", "most_bookmarks"],
            ),
            OpenApiParameter(name="is_closed", type=bool, description="마감 여부"),
        ],
        responses={
            200: RecruitmentListSerializer(many=True),
            400: RESPONSE_SCHEMAS["400_BAD_REQUEST"],
            401: RESPONSE_SCHEMAS["401_UNAUTHORIZED"],
            403: RESPONSE_SCHEMAS["403_FORBIDDEN"],
            404: RESPONSE_SCHEMAS["404_PAGE_NOT_FOUND"],
        },
        tags=["Recruitment"],
    )
    def get(self, request: Request) -> Response:
        queryset = RecruitmentService.get_filtered_recruitments(
            base_filter=Q(author=request.user),
            search=request.query_params.get("search"),
            is_closed=request.query_params.get("is_closed"),
            sort=request.query_params.get("sort", "latest"),
            allow_oldest=False,
        )

        pageable = Pageable.from_params(request.query_params.get("page"), request.query_params.get("page_size"))
        page = offset_paginate_queryset(queryset, pageable)

        serializer = RecruitmentListSerializer(page.items, many=True)
        response_data = build_paginated_response(request, page, list(serializer.data))

        return Response(response_data, status=status.HTTP_200_OK)


class RecruitmentDetailUpdateDeleteView(APIView):
    """공고 상세 조회/수정/삭제 API"""

    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="공고 상세 조회",
        description="공고의 상세 정보를 조회합니다.",
        responses={
            200: RecruitmentDetailSerializer,
            404: RESPONSE_SCHEMAS["404_NOT_FOUND"],
        },
        tags=["Recruitment"],
    )
    def get(self, request: Request, recruitments_uuid: UUID) -> Response:
        recruitment = RecruitmentService.get_recruitment_detail(recruitments_uuid)
        RecruitmentService.increment_view_count(recruitments_uuid)

        serializer = RecruitmentDetailSerializer(recruitment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="공고 수정",
        description="공고를 수정합니다. 작성자만 가능합니다.",
        request=RecruitmentUpdateSerializer,
        responses={
            200: RecruitmentDetailSerializer,
            400: RESPONSE_SCHEMAS["400_VALIDATION_ERROR"],
            401: RESPONSE_SCHEMAS["401_UNAUTHORIZED"],
            403: RESPONSE_SCHEMAS["403_FORBIDDEN"],
            404: RESPONSE_SCHEMAS["404_NOT_FOUND"],
        },
        tags=["Recruitment"],
    )
    def patch(self, request: Request, recruitments_uuid: UUID) -> Response:
        serializer = RecruitmentUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user = cast(User, request.user)
        updated_recruitment = RecruitmentService.update_recruitment(
            uuid=recruitments_uuid, user=user, validated_data=serializer.validated_data
        )

        response_data = RecruitmentService.build_update_response_data(updated_recruitment)
        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="공고 마감",
        description="공고를 마감합니다. 작성자만 가능합니다.",
        responses={
            200: {
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "공고가 삭제되었습니다."}},
            },
            401: RESPONSE_SCHEMAS["401_UNAUTHORIZED"],
            403: RESPONSE_SCHEMAS["403_FORBIDDEN"],
            404: RESPONSE_SCHEMAS["404_NOT_FOUND"],
        },
        tags=["Recruitment"],
    )
    def delete(self, request: Request, recruitments_uuid: UUID) -> Response:
        user = cast(User, request.user)
        RecruitmentService.delete_recruitment(uuid=recruitments_uuid, user=user)
        return Response({"detail": SUCCESS_MESSAGES["RECRUITMENT_DELETED"]}, status=status.HTTP_200_OK)
