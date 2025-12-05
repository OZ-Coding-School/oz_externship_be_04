from typing import Any

from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_groups.models import StudyGroup
from apps.study_groups.serializers.study_group import (
    StudyGroupDetailSerializer,
    StudyGroupListSerializer,
    StudyGroupSerializer,
)


# 스터디 그룹 만들기
class StudyGroupCreateAPIView(APIView):
    @extend_schema(
        summary="스터디 그룹 생성 REQ-STDY-0001(POST)",
        description="스터디 그룹 생성",
        request=StudyGroupSerializer,
        responses={201: StudyGroupSerializer, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        tags=["StudyGroups"],
    )
    def post(self, request: Request) -> Response:
        serializer = StudyGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        study_group = serializer.save()
        return Response(StudyGroupSerializer(study_group).data, status=status.HTTP_201_CREATED)

# 스터디 그룹 목록 보기
class StudyGroupListAPIView(APIView):
    @extend_schema(
        summary="스터디 그룹 목록 조회 REQ-STDY-0002(GET)",
        description="스터디 그룹 목록 조회",
        responses=StudyGroupListSerializer,
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                description="스터디 그룹 상태 필터",
                required=False,
                enum=["PENDING", "ONGOING", "ENDED"],
                default="PENDING",
            ),
        ],
        tags=["StudyGroups"],
    )
    def get(self, request: Request) -> Response:
        status_filter = request.query_params.get("status")
        queryset = StudyGroup.objects.all()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        serializer = StudyGroupListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

# 스터디 그룹 상세정보 조회
class StudyGroupRetrieveAPIView(APIView):
    @extend_schema(
        summary="스터디 그룹 상세 조회 REQ-STDY-0003(GET)",
        description="스터디 그룹 상세 조회",
        responses={200: StudyGroupDetailSerializer, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        tags=["StudyGroups"],
    )
    def get(self, request: Request, pk: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=pk)
        serializer = StudyGroupDetailSerializer(study_group, context={"request": request})
        return Response(serializer.data)

# 스터디 그룹 수정(업데이트)하기
class StudyGroupUpdateAPIView(APIView):
    @extend_schema(
        summary="스터디 그룹 수정 REQ-STDY-0004(PATCH)",
        description="스터디 그룹 수정",
        request=StudyGroupSerializer,
        responses={200: StudyGroupSerializer, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        tags=["StudyGroups"],
    )
    def patch(self, request: Request, pk: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=pk)
        serializer = StudyGroupSerializer(study_group, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        study_group = serializer.save()
        return Response(StudyGroupSerializer(study_group).data)

#스터디그룹 삭제하기
class StudyGroupDestroyAPIView(APIView):
    @extend_schema(
        summary="스터디 그룹 삭제 REQ-STDY-0005(DELETE)",
        description="스터디 그룹 삭제",
        responses={200: OpenApiTypes.OBJECT},
        tags=["StudyGroups"],
    )
    def delete(self, request: Request, pk: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=pk)
        study_group.delete()
        return Response({"detail": "스터디 그룹이 삭제되었습니다."}, status=status.HTTP_200_OK)
