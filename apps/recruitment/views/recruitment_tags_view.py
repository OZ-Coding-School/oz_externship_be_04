from typing import List

from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recruitment.models import Recruitment, RecruitmentTag, Tag
from apps.recruitment.serializers.tags import (
    RecruitmentTagUpdateSerializer,
    TagSerializer,
)


class RecruitmentTagAPIView(APIView):
    """
    특정 공고에 연결된 태그 조회 및 수정
    - GET: 공고 태그 조회
    - PUT: 공고 태그 전체 교체 (최대 5개)
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=["Recruitment"],
        summary="공고의 태그 조회",
        description="공고에 연결된 태그를 모두 조회합니다. (최대 5개)",
        responses={
            200: TagSerializer,
            401: {"error_detail": "인증되지 않은 사용자입니다."},
            404: {"error_detail": "해당 공고를 찾을 수 없습니다."},
        },
    )
    def get(self, request: Request, recruitment_uuid: str) -> Response:
        try:
            recruitment = Recruitment.objects.get(uuid=recruitment_uuid)
        except Recruitment.DoesNotExist:
            return Response({"error_detail": "해당 공고를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        tags = Tag.objects.filter(
            id__in=RecruitmentTag.objects.filter(recruitment=recruitment).values_list("tag_id", flat=True)
        )

        serializer = TagSerializer(tags, many=True)
        return Response({"recruitment_id": recruitment.id, "tags": serializer.data}, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Recruitment"],
        summary="공고 태그 수정",
        description="선택한 태그들로 기존 공고 태그를 수정합니다. (최대 5개)",
        request=RecruitmentTagUpdateSerializer,
        responses={
            200: TagSerializer,
            400: {"error_detail": "태그는 1개 이상, 5개 이하, 중복 없이 작성해야 합니다."},
            401: {"error_detail": "인증되지 않은 사용자입니다."},
            403: {"error_detail": "권한이 없습니다."},
            404: {"error_detail": "해당 공고를 찾을 수 없습니다."},
        },
    )
    def put(self, request: Request, recruitment_uuid: str) -> Response:
        try:
            recruitment = Recruitment.objects.get(uuid=recruitment_uuid)
        except Recruitment.DoesNotExist:
            return Response({"error_detail": "해당 공고를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        serializer = RecruitmentTagUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tag_ids: List[int] = serializer.validated_data["tags"]
        tags = Tag.objects.filter(id__in=tag_ids)

        # 선택한 태그와 DB 태그 수가 일치하지 않으면 존재하지 않는 태그 ID 포함
        if len(tags) != len(tag_ids):
            return Response(
                {"error_detail": "존재하지 않는 태그 ID가 포함되어 있습니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        # 공고 태그 전체 교체
        RecruitmentTag.objects.filter(recruitment=recruitment).delete()
        RecruitmentTag.objects.bulk_create([RecruitmentTag(recruitment=recruitment, tag=tag) for tag in tags])

        tag_serializer = TagSerializer(tags, many=True)
        return Response(
            {"detail": "공고 태그가 정상적으로 업데이트 되었습니다.", "tags": tag_serializer.data},
            status=status.HTTP_200_OK,
        )
