from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models import CrawledLecture
from apps.lectures.serializers.crawled_lecture_serializer import (
    CrawledLectureSerializer,
)


class CrawledLectureListAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CrawledLectureSerializer
    pagination_class = PageNumberPagination

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
                name="latest",
                type=OpenApiTypes.STR,
                location="query",
                description="최신순으로 정렬할 때 선택됩니다.",
                required=False,
            ),
            OpenApiParameter(
                name="oldest",
                type=OpenApiTypes.STR,
                location="query",
                description="오래된순으로 정렬할 때 선택됩니다.",
                required=False,
            ),
            OpenApiParameter(
                name="low_price",
                type=OpenApiTypes.STR,
                location="query",
                description="낮은 가격순으로 정렬할 때 선택됩니다.",
                required=False,
            ),
            OpenApiParameter(
                name="high_price",
                type=OpenApiTypes.STR,
                location="query",
                description="높은 가격순으로 정렬할 때 선택됩니다.",
                required=False,
            ),
            OpenApiParameter(
                name="high_rating",
                type=OpenApiTypes.STR,
                location="query",
                description="높은 리뷰 평점순으로 정렬할 때 선택됩니다.",
                required=False,
            ),
            OpenApiParameter(
                name="low_rating",
                type=OpenApiTypes.STR,
                location="query",
                description="낮은 리뷰 평점순으로 정렬할 때 선택됩니다.",
                required=False,
            ),
        ],
        responses={
            200: CrawledLectureSerializer(many=True, read_only=True),
            500: {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."},
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
        page: list[CrawledLecture] | None = paginator.paginate_queryset(mock_data, request)  # type: ignore[arg-type]
        serializer = self.serializer_class(page, many=True)
        return paginator.get_paginated_response(serializer.data)
