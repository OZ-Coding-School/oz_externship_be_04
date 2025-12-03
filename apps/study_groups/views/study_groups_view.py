from typing import Any, Type

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.serializers import Serializer

from apps.study_groups.models import StudyGroup
from apps.study_groups.serializers.study_group import (
    StudyGroupDetailSerializer,
    StudyGroupListSerializer,
    StudyGroupSerializer,
)


# CRUD specAPI
@extend_schema_view(
    create=extend_schema(
        summary="스터디 그룹 생성 REQ-STDY-0001(POST)",
        description="스터디 그룹 생성",
        request=StudyGroupSerializer,
        responses={
            201: StudyGroupSerializer,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        tags=["StudyGroups"],
    ),
    list=extend_schema(
        summary="스터디 그룹 목록 조회 REQ-STDY-0002(GET)",
        description="스터디 그룹 목록 조회",
        responses=StudyGroupListSerializer,
        tags=["StudyGroups"],
        parameters=[
            OpenApiParameter(
                name="status",
                type=OpenApiTypes.STR,
                description="스터디 그룹 목록 조회",
                required=False,
                enum=["PENDING", "ONGOING", "ENDED"],
                default="PENDING",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="스터디 그룹 상세 조회 REQ-STDY-0003(GET)",
        description="스터디 그룹 상세 조회",
        responses={
            200: StudyGroupDetailSerializer,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        tags=["StudyGroups"],
    ),
    update=extend_schema(
        summary="스터디 그룹 수정 REQ-STDY-0004(PATCH)",
        description="스터디 그룹 수정",
        request=StudyGroupSerializer,
        responses={
            200: StudyGroupSerializer,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
        tags=["StudyGroups"],
    ),
    ### patch로 자동 생성된 partial_update 쪽에도 summary 추가 및 스터디그룹 태그 포함하기 위해 작성
    partial_update=extend_schema(
        summary="스터디 그룹 수정 REQ-STDY-0004(PATCH)",
        tags=["StudyGroups"],
    ),
    destroy=extend_schema(
        summary="스터디 그룹 삭제 REQ-STDY-0005(DELETE)",
        description="스터디 그룹 삭제",
        responses={200: OpenApiTypes.OBJECT},
        tags=["StudyGroups"],
    ),
)
class StudyGroupViewSet(viewsets.ModelViewSet[StudyGroup]):
    queryset = StudyGroup.objects.all()
    serializer_class = StudyGroupSerializer

    def get_serializer_class(self) -> Type[Serializer[Any]]:
        if self.action == "list":
            return StudyGroupListSerializer
        if self.action == "retrieve":
            return StudyGroupDetailSerializer
        return StudyGroupSerializer
