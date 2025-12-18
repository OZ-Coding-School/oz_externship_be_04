from urllib.parse import urlencode

from django.db.models import Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import Pageable, offset_paginate_queryset
from apps.study_groups.models import Review
from apps.study_groups.serializers.admin_review_serializer import (
    AdminStudyReviewDetailSerializer,
    AdminStudyReviewListItemSerializer,
)


class AdminStudyReviewDetailAPIView(APIView):
    def _error(self, message: str, http_status: int) -> Response:
        return Response({"error_detail": message}, status=http_status)

    def _check_admin_or_response(self, request: Request) -> Response | None:
        if not request.user.is_authenticated:
            return self._error("자격 인증 데이터가 제공되지 않았습니다.", status.HTTP_401_UNAUTHORIZED)

        # admin 권한: is_staff 또는 is_superuser
        if not (getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False)):
            return self._error("권한이 없습니다.", status.HTTP_403_FORBIDDEN)

        return None

    @extend_schema(
        summary="관리자 스터디 리뷰 상세 조회",
        tags=["StudyGroup"],
    )
    def get(self, request: Request, review_id: int) -> Response:
        try:
            permission_error = self._check_admin_or_response(request)
            if permission_error:
                return permission_error

            try:
                review = Review.objects.select_related("study_group", "user").get(id=review_id)
            except Review.DoesNotExist:
                return self._error("스터디 리뷰를 찾을 수 없습니다.", status.HTTP_404_NOT_FOUND)

            serializer = AdminStudyReviewDetailSerializer(review)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception:
            return Response(
                {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminStudyReviewListAPIView(APIView):
    def _error(self, message: str, http_status: int) -> Response:
        return Response({"error_detail": message}, status=http_status)

    def _check_admin_or_response(self, request: Request) -> Response | None:
        # Detail API와 “동일 조건” 유지
        if not request.user.is_authenticated:
            return self._error("자격 인증 데이터가 제공되지 않았습니다.", status.HTTP_401_UNAUTHORIZED)

        if not (getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False)):
            return self._error("권한이 없습니다.", status.HTTP_403_FORBIDDEN)

        return None

    def _apply_search(self, qs, search: str | None):
        if not search:
            return qs
        keyword = search.strip()
        if not keyword:
            return qs

        # 검색 범위: content, 작성자 닉네임/이메일, 스터디그룹명
        return qs.filter(
            Q(content__icontains=keyword)
            | Q(user__nickname__icontains=keyword)
            | Q(user__email__icontains=keyword)
            | Q(study_group__name__icontains=keyword)
        )

    def _apply_sort(self, qs, sort: str | None):
        # sort: latest | oldest (그 외는 latest로 처리)
        if sort == "oldest":
            return qs.order_by("created_at", "id")
        return qs.order_by("-created_at", "-id")

    def _build_page_link(self, request: Request, page: int) -> str:
        params = request.query_params.copy()
        params["page"] = str(page)

        # QueryDict -> urlencode
        query = urlencode(list(params.items()))
        base = request.build_absolute_uri(request.path)
        return f"{base}?{query}" if query else base

    @extend_schema(
        summary="관리자 스터디 리뷰 목록 조회",
        tags=["Admin"],
        parameters=[
            OpenApiParameter(name="page", type=OpenApiTypes.INT, required=False),
            OpenApiParameter(name="page_size", type=OpenApiTypes.INT, required=False),
            OpenApiParameter(name="search", type=OpenApiTypes.STR, required=False),
            OpenApiParameter(
                name="sort",
                type=OpenApiTypes.STR,
                required=False,
                description='정렬: "latest" | "oldest"',
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        try:
            permission_error = self._check_admin_or_response(request)
            if permission_error:
                return permission_error

            qs = Review.objects.select_related("study_group", "user").all()

            # query params
            search = request.query_params.get("search")
            sort = request.query_params.get("sort")
            qs = self._apply_search(qs, search)
            qs = self._apply_sort(qs, sort)

            # 팀 내 pagination 사용
            pageable = Pageable.from_params(
                page_raw=request.query_params.get("page"),
                size_raw=request.query_params.get("page_size"),
            )
            page_obj = offset_paginate_queryset(qs, pageable)

            serializer = AdminStudyReviewListItemSerializer(page_obj.items, many=True)

            next_url = self._build_page_link(request, page_obj.current_page + 1) if page_obj.has_next else None
            prev_url = self._build_page_link(request, page_obj.current_page - 1) if page_obj.has_prev else None

            return Response(
                {
                    "count": page_obj.total_count,
                    "next": next_url,
                    "previous": prev_url,
                    "results": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception:
            return Response(
                {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
