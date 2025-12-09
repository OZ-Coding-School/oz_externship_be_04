from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Count, F, Q, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
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
    "PERMISSION_DENIED": "권한이 없습니다.",
    "RECRUITMENT_CLOSED": "마감된 공고는 수정/삭제할 수 없습니다.",
    "PAGE_NOT_FOUND": "요청한 페이지를 찾을 수 없습니다.",
    "INVALID_PAGE": "page 값이 유효하지 않습니다.",
    "UNAUTHENTICATED": "자격 인증 데이터가 제공되지 않았습니다.",
}

SUCCESS_MESSAGES = {
    "RECRUITMENT_CREATED": "공고가 작성되었습니다.",
    "RECRUITMENT_DELETED": "공고가 삭제되었습니다.",
}


def error_response(message: str, status_code: int) -> Response:
    return Response({"error_detail": message}, status=status_code)


def success_response(message: str, status_code: int = status.HTTP_200_OK) -> Response:
    return Response({"detail": message}, status=status_code)


def get_recruitment_queryset(
    base_filter: Q,
    include_attachments: bool = False,
) -> QuerySet[Recruitment]:
    queryset = (
        Recruitment.objects.filter(base_filter)
        .select_related("study_group", "author")
        .prefetch_related(
            "images",
            "recruitment_tags__tag",
            "study_group__studylecture_set__lecture",
        )
        .annotate(bookmark_count=Count("recruitment_bookmarks"))
    )

    if include_attachments:
        queryset = queryset.prefetch_related("attachments")

    return queryset


def apply_filters_and_sorting(
    queryset: QuerySet[Recruitment],
    search: Optional[str] = None,
    tags: Optional[str] = None,
    is_closed: Optional[str] = None,
    sort: str = "latest",
    allow_oldest: bool = True,
) -> QuerySet[Recruitment]:
    if search:
        queryset = queryset.filter(Q(title__icontains=search) | Q(content__icontains=search))

    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        queryset = queryset.filter(recruitment_tags__tag__name__in=tag_list).distinct()

    if is_closed is not None:
        is_closed_bool = is_closed.lower() in ["true", "1", "yes"]
        queryset = queryset.filter(is_closed=is_closed_bool)

    sort_map = {
        "latest": "-created_at",
        "most_views": "-views_count",
        "most_bookmarks": "-bookmark_count",
    }
    if allow_oldest:
        sort_map["oldest"] = "created_at"

    order_by = sort_map.get(sort, "-created_at")
    return queryset.order_by(order_by)


def build_paginated_response(
    page: OffsetPage[Recruitment],
    serializer_class: type,
    request: Request,
) -> dict[str, Any]:
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


def save_recruitment_relations(
    recruitment: Recruitment,
    tags: list[Tag],
    files: list[dict[str, str]],
    image_urls: list[str],
) -> None:
    if tags:
        RecruitmentTag.objects.bulk_create(
            [RecruitmentTag(recruitment=recruitment, tag=tag) for tag in tags],
            ignore_conflicts=True,
        )

    if files:
        RecruitmentAttachment.objects.bulk_create(
            [
                RecruitmentAttachment(
                    recruitment=recruitment,
                    file_name=file_data["file_name"],
                    file_url=file_data["file_url"],
                )
                for file_data in files
            ]
        )

    if image_urls:
        RecruitmentImage.objects.bulk_create(
            [RecruitmentImage(recruitment=recruitment, img_url=url) for url in image_urls]
        )


def update_recruitment_relations(
    recruitment: Recruitment,
    tags: Optional[list[Tag]],
    files: Optional[list[dict[str, str]]],
    image_urls: Optional[list[str]],
) -> None:
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


def validate_recruitment_access(recruitment: Recruitment, user: User) -> None:
    if recruitment.author != user:
        raise PermissionDenied(ERROR_MESSAGES["PERMISSION_DENIED"])

    if recruitment.is_closed:
        raise ValidationError({"error_detail": ERROR_MESSAGES["RECRUITMENT_CLOSED"]})


class RecruitmentListCreateView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="공고 목록 조회",
        description="전체 모집 공고 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(name="page", type=int, description="페이지 번호"),
            OpenApiParameter(name="size", type=int, description="페이지 크기"),
            OpenApiParameter(name="search", type=str, description="검색 키워드"),
            OpenApiParameter(
                name="sort",
                type=str,
                description="정렬",
                enum=["latest", "oldest", "most_views", "most_bookmarks"],
            ),
            OpenApiParameter(name="tags", type=str, description="태그 (쉼표 구분)"),
        ],
        responses={
            200: RecruitmentListSerializer(many=True),
            400: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "page 값이 유효하지 않습니다."}},
            },
            404: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "요청한 페이지를 찾을 수 없습니다."}},
            },
        },
        tags=["Recruitments"],
    )
    def get(self, request: Request) -> Response:
        queryset = get_recruitment_queryset(Q(is_closed=False))
        queryset = apply_filters_and_sorting(
            queryset,
            search=request.query_params.get("search"),
            tags=request.query_params.get("tags"),
            sort=request.query_params.get("sort", "latest"),
            allow_oldest=True,
        )

        pageable = Pageable.from_params(
            request.query_params.get("page"),
            request.query_params.get("size"),
        )
        page = offset_paginate_queryset(queryset, pageable)

        response_data = build_paginated_response(page, RecruitmentListSerializer, request)
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
            400: {
                "type": "object",
                "properties": {
                    "error_detail": {
                        "type": "object",
                        "example": {"content": ["내용은 공백일 수 없습니다."]},
                    }
                },
            },
            401: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "자격 인증 데이터가 제공되지 않았습니다."}},
            },
            403: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "권한이 없습니다."}},
            },
            404: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "스터디 그룹을 찾을 수 없습니다."}},
            },
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

        return success_response(SUCCESS_MESSAGES["RECRUITMENT_CREATED"], status.HTTP_200_OK)


class RecruitmentMineView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내가 작성한 공고 목록",
        description="사용자가 작성한 공고 목록을 조회합니다.",
        parameters=[
            OpenApiParameter(name="page", type=int, description="페이지 번호"),
            OpenApiParameter(name="size", type=int, description="페이지 크기"),
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
            400: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "page 값이 유효하지 않습니다."}},
            },
            401: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "자격 인증 데이터가 제공되지 않았습니다."}},
            },
            403: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "권한이 없습니다."}},
            },
            404: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "요청한 페이지를 찾을 수 없습니다."}},
            },
        },
        tags=["Recruitments"],
    )
    def get(self, request: Request) -> Response:
        user = request.user
        assert isinstance(user, User)

        queryset = get_recruitment_queryset(Q(author=user))
        queryset = apply_filters_and_sorting(
            queryset,
            search=request.query_params.get("search"),
            is_closed=request.query_params.get("is_closed"),
            sort=request.query_params.get("sort", "latest"),
            allow_oldest=False,
        )

        pageable = Pageable.from_params(
            request.query_params.get("page"),
            request.query_params.get("size"),
        )
        page = offset_paginate_queryset(queryset, pageable)

        response_data = build_paginated_response(page, RecruitmentListSerializer, request)
        return Response(response_data, status=status.HTTP_200_OK)


class RecruitmentDetailUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        summary="공고 상세 조회",
        description="공고의 상세 정보를 조회합니다.",
        responses={
            200: RecruitmentDetailSerializer,
            404: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "해당 공고를 찾을 수 없습니다."}},
            },
        },
        tags=["Recruitments"],
    )
    def get(self, request: Request, recruitments_uuid: UUID) -> Response:
        recruitment = get_object_or_404(
            get_recruitment_queryset(Q(uuid=recruitments_uuid), include_attachments=True)
        )

        Recruitment.objects.filter(uuid=recruitments_uuid).update(
            views_count=F("views_count") + 1
        )

        serializer = RecruitmentDetailSerializer(recruitment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="공고 수정",
        description="공고를 수정합니다. 작성자만 가능합니다.",
        request=RecruitmentUpdateSerializer,
        responses={
            200: RecruitmentDetailSerializer,
            400: {
                "type": "object",
                "properties": {
                    "error_detail": {
                        "type": "object",
                        "example": {"content": ["내용은 공백일 수 없습니다."]},
                    }
                },
            },
            401: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "자격 인증 데이터가 제공되지 않았습니다."}},
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
        tags=["Recruitments"],
    )
    @transaction.atomic
    def patch(self, request: Request, recruitments_uuid: UUID) -> Response:
        user = request.user
        assert isinstance(user, User)

        recruitment = get_object_or_404(Recruitment, uuid=recruitments_uuid)
        validate_recruitment_access(recruitment, user)

        serializer = RecruitmentUpdateSerializer(recruitment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        tags = serializer.validated_data.pop("tags", None)
        files = serializer.validated_data.pop("files", None)
        image_urls = serializer.validated_data.pop("image_urls", None)

        recruitment = serializer.save()
        update_recruitment_relations(recruitment, tags, files, image_urls)

        recruitment = get_object_or_404(
            get_recruitment_queryset(Q(uuid=recruitments_uuid), include_attachments=True)
        )

        return Response(
            RecruitmentDetailSerializer(recruitment).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="공고 삭제",
        description="공고를 삭제합니다. 작성자만 가능합니다.",
        responses={
            200: {
                "type": "object",
                "properties": {"detail": {"type": "string", "example": "공고가 삭제되었습니다."}},
            },
            401: {
                "type": "object",
                "properties": {"error_detail": {"type": "string", "example": "자격 인증 데이터가 제공되지 않았습니다."}},
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
        tags=["Recruitments"],
    )
    @transaction.atomic
    def delete(self, request: Request, recruitments_uuid: UUID) -> Response:
        user = request.user
        assert isinstance(user, User)

        recruitment = get_object_or_404(Recruitment, uuid=recruitments_uuid)
        validate_recruitment_access(recruitment, user)

        recruitment.is_closed = True
        recruitment.save(update_fields=["is_closed"])

        return success_response(SUCCESS_MESSAGES["RECRUITMENT_DELETED"])