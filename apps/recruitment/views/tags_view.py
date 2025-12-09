from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recruitment.serializers.tags import TagSerializer
from apps.recruitment.services.tags_service import TagService


class TagPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"


class TagListAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=["tags"],
        summary="태그 검색 및 조회하는 API 입니다.",
        description=(
            "태그명을 일부 검색하거나 완전 일치하는 항목을 확인할수 있습니다.\n\n"
            "페이지당 5개의 태그를 확인할 수 있습니다."
        ),
        parameters=[
            OpenApiParameter(
                name="keyword", description="검색할 키워드 (부분/완전 일치 검색 가능)", required=False, type=str
            ),
            OpenApiParameter(name="page", description="페이지 번호로 조회할수 있습니다.", required=False, type=int),
        ],
        responses={
            200: TagSerializer(many=True),
            404: {"error_detail": "요청한 페이지를 찾을 수 없습니다."},
        },
    )
    def get(self, request: Request) -> Response:
        keyword = request.GET.get("keyword", "").strip()
        queryset = TagService.get_tags(keyword=keyword)

        paginator = TagPagination()
        page = paginator.paginate_queryset(queryset, request)

        if page is None:
            return Response(
                {"error_detail": "요청한 페이지를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TagSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        tags=["tags"],
        summary="태그 생성 API 입니다.",
        description=("존재하지 않을 경우, 태그를 생성 할수 있습니다."),
        request=TagSerializer,
        responses={
            201: {"detail": "태그가 정상적으로 등록되었습니다."},
            409: {"error_detail": "이미 존재하는 태그입니다."},
            401: {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
        },
    )
    def post(self, request: Request) -> Response:
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"error_detail": "자격 인증 데이터가 제공되지 않았습니다."}, status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = TagSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            tag = serializer.save()
        except ValidationError:
            return Response(
                {"error_detail": "이미 존재하는 태그입니다."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            {
                "detail": f"태그 '{tag.name}'가 정상적으로 등록되었습니다.",
                "tag": TagSerializer(tag).data,
            },
            status=status.HTTP_201_CREATED,
        )
