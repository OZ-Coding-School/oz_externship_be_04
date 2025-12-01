from __future__ import annotations

from typing import cast

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
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
from apps.application.serializers.cancel_application_serializers import (
    ApplicationCancelSerializer,
)
from apps.users.models import User


class ApplicationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="지원서 제출",
        request=ApplicationCreateSerializer,
        responses={200: dict},
        tags=["Application - Applicant"],
    )
    def post(self, request: Request, recruitment_uuid: str) -> Response:
        serializer = ApplicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = cast(User, request.user)

        Application.objects.create(
            applicant=user,
            recruitment_id=recruitment_uuid,
            **serializer.validated_data,
        )

        return Response({"detail": "지원이 완료되었습니다."}, status=status.HTTP_200_OK)


class MyApplicationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 지원 목록 조회 (cursor)",
        parameters=[
            OpenApiParameter("cursor", OpenApiTypes.STR, required=False),
            OpenApiParameter("page_size", OpenApiTypes.INT, required=False),
        ],
        responses={200: ApplicantApplicationListSerializer},
        tags=["Application - Applicant"],
    )
    def get(self, request: Request) -> Response:
        user = cast(User, request.user)

        applications = Application.objects.filter(applicant=user).order_by("-created_at")

        serializer = ApplicantApplicationListSerializer(applications, many=True)

        return Response({"next": None, "previous": None, "results": serializer.data})


class MyApplicationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 지원 상세 조회",
        responses={200: ApplicantApplicationDetailSerializer},
        tags=["Application - Applicant"],
    )
    def get(self, request: Request, application_uuid: str) -> Response:
        user = cast(User, request.user)

        application = Application.objects.filter(uuid=application_uuid, applicant=user).first()

        if application is None:
            return Response(
                {"error_detail": "해당 지원서를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ApplicantApplicationDetailSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApplicationCancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="지원 취소",
        responses={200: ApplicationCancelSerializer},
        tags=["Application - Applicant"],
    )
    def post(self, request: Request, application_uuid: str) -> Response:
        user = cast(User, request.user)

        application = Application.objects.filter(uuid=application_uuid, applicant=user).first()

        if application is None:
            return Response(
                {"error_detail": "해당 지원서를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        application.status = ApplicationStatus.CANCELED
        application.save(update_fields=["status"])

        serializer = ApplicationCancelSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)
