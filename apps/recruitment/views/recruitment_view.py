from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Count, F, Q, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import OffsetPage, Pageable, offset_paginate_queryset
from apps.recruitment.models import (
    Recruitment,
    RecruitmentAttachment,
    RecruitmentImage,
    RecruitmentTag,
    Tag,
)
from apps.recruitment.serializers import (
    RecruitmentCreateSerializer,
    RecruitmentDetailSerializer,
    RecruitmentListSerializer,
    RecruitmentUpdateSerializer,
)
from apps.users.models import User

ERROR_MESSAGES = {
    "RECRUITMENT_NOT_FOUND": "해당 공고를 찾을 수 없습니다.",
    "STUDY_GROUP_NOT_FOUND": "스터디 그룹을 찾을 수 없습니다.",
    "PERMISSION_DENIED": "권한이 없습니다.",
    "RECRUITMENT_CLOSED": "마감된 공고는 수정할 수 없습니다.",
    "ALREADY_CLOSED": "이미 마감된 공고입니다.",
    "UNAUTHENTICATED": "자격 인증 데이터가 제공되지 않았습니다.",
}

SUCCESS_MESSAGES = {
    "RECRUITMENT_CREATED": "공고가 작성되었습니다.",
    "RECRUITMENT_DELETED": "공고가 삭제되었습니다.",
}


def error_response(message: str, status_code: int) -> Response:
    """에러 응답 생성"""
    return Response({"error_detail": message}, status=status_code)


def success_response(message: str, status_code: int = status.HTTP_200_OK) -> Response:
    """성공 응답 생성"""
    return Response({"detail": message}, status=status_code)


def get_base_recruitment_queryset(extra_filters: Optional[Q] = None) -> QuerySet[Recruitment]:
    """
    공고 조회용 기본 queryset 생성
    - select_related, prefetch_related 최적화
    - bookmark_count annotate
    """
    queryset = (
        Recruitment.objects.select_related("study_group", "author")
        .prefetch_related("images", "recruitment_tags__tag", "study_group__studylecture_set__lecture")
        .annotate(bookmark_count=Count("recruitment_bookmarks"))
    )

    if extra_filters:
        queryset = queryset.filter(extra_filters)

    return queryset


def get_recruitment_detail_queryset(recruitment_uuid: UUID) -> Recruitment:
    """
    공고 상세 조회용 queryset
    attachments prefetch 포함
    """
    return get_object_or_404(
        Recruitment.objects.select_related("study_group", "author")
        .prefetch_related("images", "attachments", "recruitment_tags__tag", "study_group__studylecture_set__lecture")
        .annotate(bookmark_count=Count("recruitment_bookmarks")),
        uuid=recruitment_uuid,
    )


def apply_search_filter(queryset: QuerySet[Recruitment], search: Optional[str]) -> QuerySet[Recruitment]:
    """검색 필터 적용 (제목/내용)"""
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(content__icontains=search))
    return queryset


def apply_tags_filter(queryset: QuerySet[Recruitment], tags: Optional[str]) -> QuerySet[Recruitment]:
    """태그 필터 적용"""
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        queryset = queryset.filter(recruitment_tags__tag__name__in=tag_list).distinct()
    return queryset


def apply_sorting(queryset: QuerySet[Recruitment], sort: str, allow_oldest: bool = True) -> QuerySet[Recruitment]:
    """정렬 적용"""
    if sort == "latest":
        return queryset.order_by("-created_at")
    elif sort == "oldest" and allow_oldest:
        return queryset.order_by("created_at")
    elif sort == "most_views":
        return queryset.order_by("-views_count")
    elif sort == "most_bookmarks":
        return queryset.order_by("-bookmark_count")
    return queryset.order_by("-created_at")


def save_recruitment_relations(
    recruitment: Recruitment, tags: list[Tag], files: list[dict[str, str]], image_urls: list[str]
) -> None:
    """
    공고 관련 데이터 저장 (태그, 파일, 이미지)
    CreateView와 UpdateView에서 공통 사용
    """
    if tags:
        RecruitmentTag.objects.bulk_create(
            [RecruitmentTag(recruitment=recruitment, tag=tag) for tag in tags], ignore_conflicts=True
        )

    if files:
        RecruitmentAttachment.objects.bulk_create(
            [
                RecruitmentAttachment(
                    recruitment=recruitment, file_name=file_data["file_name"], file_url=file_data["file_url"]
                )
                for file_data in files
            ]
        )

    if image_urls:
        RecruitmentImage.objects.bulk_create(
            [RecruitmentImage(recruitment=recruitment, img_url=image_url) for image_url in image_urls]
        )


def update_recruitment_relations(
    recruitment: Recruitment,
    tags: Optional[list[Tag]],
    files: Optional[list[dict[str, str]]],
    image_urls: Optional[list[str]],
) -> None:
    """
    공고 관련 데이터 업데이트 (태그, 파일, 이미지)
    기존 데이터 삭제 후 새로 생성 (전체 교체 방식)
    """
    if tags is not None:
        RecruitmentTag.objects.filter(recruitment=recruitment).delete()
        if tags:
            save_recruitment_relations(recruitment, tags, [], [])

    if files is not None:
        RecruitmentAttachment.objects.filter(recruitment=recruitment).delete()
        if files:
            save_recruitment_relations(recruitment, [], files, [])

    if image_urls is not None:
        RecruitmentImage.objects.filter(recruitment=recruitment).delete()
        if image_urls:
            save_recruitment_relations(recruitment, [], [], image_urls)


def validate_author_permission(
    recruitment: Recruitment, user: User
) -> tuple[Optional[Recruitment], Optional[Response]]:
    """
    작성자 권한 검증

    Returns:
        (recruitment, None) if valid
        (None, error_response) if invalid
    """
    if recruitment.author != user:
        return None, error_response(ERROR_MESSAGES["PERMISSION_DENIED"], status.HTTP_403_FORBIDDEN)
    return recruitment, None


def validate_recruitment_not_closed(recruitment: Recruitment) -> tuple[Optional[Recruitment], Optional[Response]]:
    """
    공고 마감 상태 검증

    Returns:
        (recruitment, None) if not closed
        (None, error_response) if closed
    """
    if recruitment.is_closed:
        return None, error_response(ERROR_MESSAGES["RECRUITMENT_CLOSED"], status.HTTP_400_BAD_REQUEST)
    return recruitment, None


def build_paginated_response(page: OffsetPage[Recruitment], serializer_class: type, request: Request) -> dict[str, Any]:
    """
    OffsetPage를 DRF 페이지네이션 응답 형식으로 변환
    명세서 형식: count, next, previous, results
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

    serializer = serializer_class(page.items, many=True)

    return {
        "count": page.total_count,
        "next": next_url,
        "previous": previous_url,
        "results": serializer.data,
    }


class RecruitmentCreateView(APIView):
    """공고 작성 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="공고 작성 (POST)",
        description="스터디 모집 공고를 작성합니다. S3에 업로드된 파일/이미지 URL을 전달합니다.",
        request=RecruitmentCreateSerializer,
        responses={
            201: RecruitmentDetailSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        tags=["Recruitments"],
    )
    @transaction.atomic
    def post(self, request: Request) -> Response:
        serializer = RecruitmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tags = serializer.validated_data.pop("tags", [])
        files = serializer.validated_data.pop("files", [])
        image_urls = serializer.validated_data.pop("image_urls", [])

        recruitment = serializer.save(author=request.user)

        save_recruitment_relations(recruitment, tags, files, image_urls)

        # 생성된 공고를 상세 정보와 함께 반환 (study_group 포함)
        recruitment = get_recruitment_detail_queryset(recruitment.uuid)
        serializer = RecruitmentDetailSerializer(recruitment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecruitmentListView(APIView):
    """공고 목록 조회 (전체) API"""

    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="공고 목록 조회 (GET)",
        description="전체 모집 공고 목록을 조회합니다. 페이지네이션, 검색, 정렬, 태그 필터를 지원합니다.",
        parameters=[
            OpenApiParameter(name="page", type=int, description="페이지 번호 (기본 1)", required=False),
            OpenApiParameter(name="size", type=int, description="페이지 크기 (기본 10)", required=False),
            OpenApiParameter(name="search", type=str, description="제목/내용 검색", required=False),
            OpenApiParameter(
                name="sort",
                type=str,
                description="정렬 기준",
                required=False,
                enum=["latest", "oldest", "most_views", "most_bookmarks"],
            ),
            OpenApiParameter(name="tags", type=str, description="태그 필터 (쉼표 구분: python,django)", required=False),
        ],
        responses={200: RecruitmentListSerializer(many=True), 400: OpenApiTypes.OBJECT},
        tags=["Recruitments"],
    )
    def get(self, request: Request) -> Response:
        queryset = get_base_recruitment_queryset(Q(is_closed=False))

        queryset = apply_search_filter(queryset, request.query_params.get("search"))
        queryset = apply_tags_filter(queryset, request.query_params.get("tags"))
        queryset = apply_sorting(queryset, request.query_params.get("sort", "latest"), allow_oldest=True)

        pageable = Pageable.from_params(request.query_params.get("page"), request.query_params.get("size"))
        page = offset_paginate_queryset(queryset, pageable)

        response_data = build_paginated_response(page, RecruitmentListSerializer, request)
        return Response(response_data, status=status.HTTP_200_OK)


class RecruitmentRecommandView(APIView):
    """추천 공고 목록 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="추천 공고 목록 (GET)",
        description="사용자 맞춤 추천 공고를 조회합니다. 배열로 반환되며 페이지네이션이 없습니다.",
        parameters=[
            OpenApiParameter(name="search", type=str, description="검색 키워드", required=False),
            OpenApiParameter(
                name="sort",
                type=str,
                description="정렬 기준",
                required=False,
                enum=["latest", "oldest", "most_views", "most_bookmarks"],
            ),
            OpenApiParameter(name="tags", type=str, description="태그 필터 (쉼표 구분)", required=False),
        ],
        responses={200: RecruitmentListSerializer(many=True), 401: OpenApiTypes.OBJECT},
        tags=["Recruitments"],
    )
    def get(self, request: Request) -> Response:
        # TODO: 실제 추천 알고리즘은 별도 서비스로 구현 필요 (담당자 구현 예정)
        queryset = get_base_recruitment_queryset(Q(is_closed=False))

        queryset = apply_search_filter(queryset, request.query_params.get("search"))
        queryset = apply_tags_filter(queryset, request.query_params.get("tags"))
        queryset = apply_sorting(queryset, request.query_params.get("sort", "latest"), allow_oldest=True)

        queryset = queryset[:20]

        serializer = RecruitmentListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecruitmentMineView(APIView):
    """내가 작성한 공고 목록 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내가 작성한 공고 목록 (GET)",
        description="사용자가 작성한 공고 목록을 조회합니다. oldest 정렬은 지원하지 않습니다.",
        parameters=[
            OpenApiParameter(name="page", type=int, description="페이지 번호 (기본 1)", required=False),
            OpenApiParameter(name="size", type=int, description="페이지 크기 (기본 10)", required=False),
            OpenApiParameter(name="search", type=str, description="검색 키워드", required=False),
            OpenApiParameter(
                name="sort",
                type=str,
                description="정렬 기준 (oldest 제외)",
                required=False,
                enum=["latest", "most_views", "most_bookmarks"],
            ),
            OpenApiParameter(name="is_closed", type=bool, description="마감 여부 필터 (true/false)", required=False),
        ],
        responses={
            200: RecruitmentListSerializer(many=True),
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        tags=["Recruitments"],
    )
    def get(self, request: Request) -> Response:
        queryset = get_base_recruitment_queryset(Q(author=request.user))

        is_closed = request.query_params.get("is_closed")
        if is_closed is not None:
            is_closed_bool = is_closed.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(is_closed=is_closed_bool)

        queryset = apply_search_filter(queryset, request.query_params.get("search"))
        queryset = apply_sorting(queryset, request.query_params.get("sort", "latest"), allow_oldest=False)

        pageable = Pageable.from_params(request.query_params.get("page"), request.query_params.get("size"))
        page = offset_paginate_queryset(queryset, pageable)

        response_data = build_paginated_response(page, RecruitmentListSerializer, request)
        return Response(response_data, status=status.HTTP_200_OK)


class RecruitmentDetailView(APIView):
    """공고 상세 조회 API"""

    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="공고 상세 조회 (GET)",
        description="공고의 상세 정보를 조회합니다. 조회 시 조회수가 자동으로 1 증가합니다.",
        responses={200: RecruitmentDetailSerializer, 404: OpenApiTypes.OBJECT},
        tags=["Recruitments"],
    )
    def get(self, request: Request, recruitments_uuid: UUID) -> Response:
        recruitment = get_recruitment_detail_queryset(recruitments_uuid)
        Recruitment.objects.filter(uuid=recruitments_uuid).update(views_count=F("views_count") + 1)
        recruitment.views_count = F("views_count") + 1

        serializer = RecruitmentDetailSerializer(recruitment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecruitmentUpdateView(APIView):
    """공고 수정 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="공고 수정 (PATCH)",
        description="공고를 수정합니다. 작성자만 수정 가능합니다. 부분 수정을 지원합니다.",
        request=RecruitmentUpdateSerializer,
        responses={
            200: RecruitmentDetailSerializer,
            400: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        tags=["Recruitments"],
    )
    @transaction.atomic
    def patch(self, request: Request, recruitments_uuid: UUID) -> Response:
        recruitment = get_object_or_404(Recruitment, uuid=recruitments_uuid)

        _, error = validate_author_permission(recruitment, request.user)
        if error:
            return error

        _, error = validate_recruitment_not_closed(recruitment)
        if error:
            return error

        serializer = RecruitmentUpdateSerializer(recruitment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        tags = serializer.validated_data.pop("tags", None)
        files = serializer.validated_data.pop("files", None)
        image_urls = serializer.validated_data.pop("image_urls", None)

        recruitment = serializer.save()

        update_recruitment_relations(recruitment, tags, files, image_urls)

        recruitment = get_recruitment_detail_queryset(recruitments_uuid)

        return Response(RecruitmentDetailSerializer(recruitment).data, status=status.HTTP_200_OK)


class RecruitmentDeleteView(APIView):
    """공고 삭제 API"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="공고 삭제 (DELETE)",
        description="공고를 삭제합니다. 작성자만 삭제 가능합니다. Soft Delete 방식으로 is_closed=True로 변경됩니다.",
        responses={
            200: {
                "type": "object",
                "properties": {"detail": {"type": "string", "example": SUCCESS_MESSAGES["RECRUITMENT_DELETED"]}},
            },
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        tags=["Recruitments"],
    )
    @transaction.atomic
    def delete(self, request: Request, recruitments_uuid: UUID) -> Response:
        recruitment = get_object_or_404(Recruitment, uuid=recruitments_uuid)

        _, error = validate_author_permission(recruitment, request.user)
        if error:
            return error

        _, error = validate_recruitment_not_closed(recruitment)
        if error:
            return error_response(ERROR_MESSAGES["ALREADY_CLOSED"], status.HTTP_400_BAD_REQUEST)

        recruitment.is_closed = True
        recruitment.save(update_fields=["is_closed"])

        return success_response(SUCCESS_MESSAGES["RECRUITMENT_DELETED"])
