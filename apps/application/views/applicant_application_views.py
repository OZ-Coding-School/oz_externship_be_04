from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.application.models import Application, ApplicationStatus
from apps.application.serializers.application_serializers import (
    ApplicantApplicationDetailSerializer,
    ApplicantApplicationListSerializer,
    ApplicationCreateSerializer,
)
from apps.recruitment.models import Recruitment
from apps.users.models import User


class ApplicationCursorPagination(CursorPagination):
    page_size = 10
    page_size_query_param = "page_size"
    ordering = "-created_at"


class ApplicationCreateView(APIView):
    """[REQ-APLY-001] 지원서 제출"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="지원서 제출",
        request=ApplicationCreateSerializer,
        tags=["Recruitments"],
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string", "example": "스터디 공고에 지원 신청이 완료되었습니다."}
                    },
                }
            ),
            404: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"error_detail": {"type": "string", "example": "해당 공고를 찾을 수 없습니다."}},
                }
            ),
            409: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {
                        "error_detail": {"type": "string", "example": "해당 공고에 이미 지원한 내역이 존재합니다."}
                    },
                }
            ),
        },
    )
    def post(self, request: Request, recruitment_uuid: str) -> Response:

        user = request.user
        assert isinstance(user, User)

        try:
            recruitment = Recruitment.objects.get(uuid=recruitment_uuid)
        except Recruitment.DoesNotExist:
            return Response({"error_detail": "해당 공고를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if Application.objects.filter(recruitment=recruitment, applicant=user).exists():
            return Response(
                {"error_detail": "해당 공고에 이미 지원한 내역이 존재합니다."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        Application.objects.create(
            recruitment=recruitment,
            applicant=user,
            **serializer.validated_data,
        )

        return Response(
            {"detail": "스터디 공고에 지원 신청이 완료되었습니다."},
            status=status.HTTP_200_OK,
        )


class MyApplicationListView(APIView):
    """[REQ-APLY-006] 내가 지원한 공고 목록 조회"""

    permission_classes = [IsAuthenticated]
    pagination_class = ApplicationCursorPagination

    @extend_schema(
        summary="내 지원 목록 조회 (cursor)",
        parameters=[
            OpenApiParameter("cursor", OpenApiTypes.STR, required=False),
            OpenApiParameter("page_size", OpenApiTypes.INT, required=False),
        ],
        responses={200: ApplicantApplicationListSerializer(many=True)},
        tags=["Recruitments"],
    )
    def get(self, request: Request) -> Response:

        user = request.user
        assert isinstance(user, User)

        queryset = Application.objects.filter(applicant=user).select_related("recruitment").order_by("-created_at")

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)

        if page is not None:
            serializer = ApplicantApplicationListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ApplicantApplicationListSerializer(queryset, many=True)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)


class MyApplicationDetailView(APIView):
    """[REQ-APLY-007] 내가 지원한 상세 조회"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 지원 상세 조회",
        responses={
            200: ApplicantApplicationDetailSerializer,
            404: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"error_detail": {"type": "string", "example": "해당 지원 내역을 찾을 수 없습니다."}},
                }
            ),
        },
        tags=["Recruitments"],
    )
    def get(self, request: Request, application_id: int) -> Response:

        user = request.user
        assert isinstance(user, User)

        application = (
            Application.objects.filter(id=application_id, applicant=user).select_related("recruitment").first()
        )

        if not application:
            return Response(
                {"error_detail": "해당 지원 내역을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ApplicantApplicationDetailSerializer(application)
        return Response(serializer.data, status=200)


class ApplicationCancelView(APIView):
    """[REQ-APLY-008] 지원 취소"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="지원 취소",
        tags=["Recruitments"],
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"detail": {"type": "string", "example": "지원 내역이 취소되었습니다."}},
                }
            ),
            404: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"error_detail": {"type": "string", "example": "해당 지원 내역을 찾을 수 없습니다."}},
                }
            ),
            403: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"error_detail": {"type": "string", "example": "권한이 없습니다."}},
                }
            ),
        },
    )
    def post(self, request: Request, application_id: int) -> Response:

        user = request.user
        assert isinstance(user, User)

        application = Application.objects.filter(id=application_id, applicant=user).first()

        if not application:
            return Response(
                {"error_detail": "해당 지원 내역을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        application.status = ApplicationStatus.CANCELED
        application.save(update_fields=["status"])

        return Response({"detail": "지원 내역이 취소되었습니다."}, status=status.HTTP_200_OK)


class ApplicationDeleteView(APIView):
    """[REQ-APLY-008] 지원 내역 삭제"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="지원 내역 삭제",
        tags=["Recruitments"],
        responses={
            200: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"detail": {"type": "string", "example": "지원 내역이 삭제되었습니다."}},
                }
            ),
            403: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"error_detail": {"type": "string", "example": "권한이 없습니다."}},
                }
            ),
            404: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"error_detail": {"type": "string", "example": "해당 지원 내역을 찾을 수 없습니다."}},
                }
            ),
        },
    )
    def delete(self, request: Request, application_id: int) -> Response:

        user = request.user
        assert isinstance(user, User)

        application = Application.objects.filter(id=application_id).first()
        if not application:
            return Response(
                {"error_detail": "해당 지원 내역을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if application.applicant != user:
            return Response(
                {"error_detail": "권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        application.delete()
        return Response(
            {"detail": "지원 내역이 삭제되었습니다."},
            status=status.HTTP_200_OK,
        )
