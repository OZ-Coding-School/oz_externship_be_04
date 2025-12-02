from typing import cast

from django.conf import settings
from django.db.models import Q, QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_field
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.filters.crawled_lecture_filter import CrawledLectureFilter
from apps.lectures.models import CrawledLecture
from apps.lectures.serializers.crawled_lecture_serializer import (
    CrawledLectureSerializer,
)


class CrawledLectureListAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CrawledLectureSerializer
    pagination_class = PageNumberPagination
    search_fields = ["title", "instructor"]
    filterset_class = CrawledLectureFilter

    sort_map = {
        "latest": "-created_at",
        "oldest": "created_at",
        "low_price": "discount_price",
        "high_price": "-discount_price",
        "high_rating": "-average_rating",
        "low_rating": "average_rating",
    }

    @extend_schema_field(dict)
    def get_queryset(self) -> QuerySet[CrawledLecture]:
        queryset = CrawledLecture.objects.all()

        filterset = self.filterset_class(data=self.request.GET, queryset=queryset, request=self.request)
        queryset = cast(QuerySet[CrawledLecture], filterset.qs)

        q = Q()
        if search := self.request.GET.get("search"):
            for field in self.search_fields:
                q |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(q)

        if (sort_key := self.request.GET.get("sort")) in self.sort_map:
            queryset = queryset.order_by(self.sort_map[sort_key])

        return queryset

    @extend_schema(
        tags=["lectures"],
        summary="크롤링된 강의 목록을 조회하는 API입니다.",
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
                description="한 페이지에 나타내는 강의 목록의 수를 조절할 수 있습니다.",
                required=False,
            ),
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location="query",
                description="강의 제목 또는 강사 이름으로 검색합니다.",
                required=False,
            ),
            OpenApiParameter(
                name="sort",
                type=OpenApiTypes.STR,
                location="query",
                enum=[
                    "latest",
                    "oldest",
                    "low_price",
                    "high_price",
                    "high_rating",
                    "low_rating",
                ],
                description="""
아래의 정렬 기준을 선택할 수 있습니다:
- latest : 최신순으로 정렬
- oldest : 오래된순으로 정렬
- low_price : 낮은 가격순으로 정렬
- high_price : 높은 가격순으로 정렬
- high_rating : 높은 리뷰 평점순으로 정렬
- low_rating : 낮은 리뷰 평점순으로 정렬
                """,
                required=False,
            ),
        ],
        responses={
            200: CrawledLectureSerializer(many=True, read_only=True),
            500: {"example": {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."}},
        },
    )
    def get(self, request: Request) -> Response:
        import random
        from decimal import Decimal

        mock_data = [
            CrawledLecture(
                id=random.randint(1, 1000),
                external_id=random.randint(1, 1000),
                title=f"제목{i}",
                instructor=f"강사{i}",
                average_rating=Decimal(random.randint(100, 500) / 100),
                total_class_time=random.randint(1, 60),
                difficulty=random.choice([difficulty[0] for difficulty in CrawledLecture.DifficultyEnum.choices]),
                platform=random.choice([platform[0] for platform in CrawledLecture.PlatformEnum.choices]),
                original_price=random.randint(1, 1000),
                discount_price=random.randint(1, 1000),
                url_link=f"https://example_url_{i}.com",
                thumbnail_img_url=f"https://example_thumbnail_{i}.com",
            )
            for i in range(15)
        ]
        paginator = self.pagination_class()
        page_size = self.request.GET.get("page_size")
        paginator.page_size = max(int(page_size), 1) if page_size and page_size.isdigit() else 12
        page: list[CrawledLecture] | None

        if settings.DEBUG:
            page = paginator.paginate_queryset(mock_data, request)  # type: ignore[arg-type]
        else:
            queryset = self.get_queryset()
            page = paginator.paginate_queryset(queryset, request)

        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)
