from django.db.models import QuerySet
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.lectures.models import CrawledLecture
from apps.lectures.serializers.crawled_lecture_serializer import (
    CrawledLectureSerializer,
)


class CrawledLectureAVIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = CrawledLectureSerializer
    pagination_class = PageNumberPagination

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
