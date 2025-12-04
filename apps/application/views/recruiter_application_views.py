from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.db.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import CursorPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.application.models import Application, ApplicationStatus
from apps.application.serializers.application_serializers import (
    RecruiterApplicationDetailSerializer,
    RecruiterApplicationListSerializer,
)
from apps.recruitment.models import Recruitment
from apps.users.models import User

ERROR_MESSAGES = {
    "RECRUITMENT_NOT_FOUND": "해당 공고를 찾을 수 없습니다.",
    "APPLICATION_NOT_FOUND": "해당 지원 내역을 찾을 수 없습니다.",
    "PERMISSION_DENIED": "권한이 없습니다.",
}

SUCCESS_MESSAGES = {
    "ACCEPTED": "지원 내역이 승인되었습니다.",
    "REJECTED": "지원 내역이 반려되었습니다.",
}


class ApplicationCursorPagination(CursorPagination):
    page_size = 10
    page_size_query_param = "page_size"
    ordering = "-created_at"


def get_authenticated_user(request: Request) -> User:
    """인증된 사용자 반환"""
    user = request.user
    if isinstance(user, AnonymousUser):
        raise PermissionDenied("로그인이 필요합니다.")
    assert isinstance(user, User)
    return user


def get_recruitment_or_none(recruitment_uuid: str) -> Optional[Recruitment]:
    """모집 공고 조회"""
    return Recruitment.objects.filter(uuid=recruitment_uuid).first()


def get_application_with_relations(application_id: int) -> Optional[Application]:
    """지원 내역 조회 (관련 데이터 함께)"""
    return Application.objects.filter(id=application_id).select_related("applicant", "recruitment").first()


def is_recruitment_author(recruitment: Recruitment, user: User) -> bool:
    """모집 공고 작성자 여부 확인"""
    return recruitment.author == user


def get_applications_for_recruitment(recruitment: Recruitment) -> QuerySet[Application]:
    """모집 공고의 지원 내역 목록 조회"""
    return Application.objects.filter(recruitment=recruitment).select_related("applicant").order_by("-created_at")


def error_response(message: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    """에러 응답 생성"""
    return Response({"error_detail": message}, status=status_code)


def success_response(message: str, status_code: int = status.HTTP_200_OK) -> Response:
    """성공 응답 생성"""
    return Response({"detail": message}, status=status_code)


class ApplicationListView(APIView):
    """[REQ-APLY-002] 작성자용 지원자 목록 조회"""

    permission_classes = [IsAuthenticated]
    pagination_class = ApplicationCursorPagination

    @extend_schema(
        summary="작성자용 지원자 목록 조회",
        description="모집 공고 작성자가 해당 공고에 지원한 지원자 목록을 조회합니다.",
        parameters=[
            OpenApiParameter("cursor", OpenApiTypes.STR, description="커서 값"),
            OpenApiParameter("page_size", OpenApiTypes.INT, description="페이지 크기 (기본값: 10)"),
        ],
        responses={200: RecruiterApplicationListSerializer(many=True)},
        tags=["Application - Recruiter"],
    )
    def get(self, request: Request, recruitment_uuid: str) -> Response:
        user = get_authenticated_user(request)

        recruitment = get_recruitment_or_none(recruitment_uuid)
        if recruitment is None:
            return error_response(ERROR_MESSAGES["RECRUITMENT_NOT_FOUND"], status.HTTP_404_NOT_FOUND)

        if not is_recruitment_author(recruitment, user):
            return error_response(ERROR_MESSAGES["PERMISSION_DENIED"], status.HTTP_403_FORBIDDEN)

        applications = get_applications_for_recruitment(recruitment)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(applications, request, view=self)
        if page is not None:
            serializer = RecruiterApplicationListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = RecruiterApplicationListSerializer(applications, many=True)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)


class ApplicationReviewView(APIView):
    """[REQ-APLY-003] 작성자용 지원자 상세 조회"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="작성자용 지원자 상세 조회",
        description="모집 공고 작성자가 지원자의 상세 정보를 조회합니다.",
        responses={200: RecruiterApplicationDetailSerializer},
        tags=["Application - Recruiter"],
    )
    def get(self, request: Request, application_id: int) -> Response:
        user = get_authenticated_user(request)

        application = get_application_with_relations(application_id)
        if application is None:
            return error_response(ERROR_MESSAGES["APPLICATION_NOT_FOUND"], status.HTTP_404_NOT_FOUND)

        if not is_recruitment_author(application.recruitment, user):
            return error_response(ERROR_MESSAGES["PERMISSION_DENIED"], status.HTTP_403_FORBIDDEN)

        serializer = RecruiterApplicationDetailSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApplicationAcceptView(APIView):
    """[REQ-APLY-004] 지원 승인"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="지원 승인",
        description="모집 공고 작성자가 지원을 승인합니다.",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Application - Recruiter"],
    )
    @transaction.atomic
    def post(self, request: Request, application_id: int) -> Response:
        user = get_authenticated_user(request)

        application = get_application_with_relations(application_id)
        if application is None:
            return error_response(ERROR_MESSAGES["APPLICATION_NOT_FOUND"], status.HTTP_404_NOT_FOUND)

        if not is_recruitment_author(application.recruitment, user):
            return error_response(ERROR_MESSAGES["PERMISSION_DENIED"], status.HTTP_403_FORBIDDEN)

        if application.status != ApplicationStatus.PENDING:
            return error_response("이미 처리된 지원입니다.", status.HTTP_400_BAD_REQUEST)

        recruitment = application.recruitment
        accepted_count = recruitment.applications.filter(status=ApplicationStatus.ACCEPTED).count()
        if accepted_count >= recruitment.expected_headcount:
            return error_response("모집 인원이 초과되었습니다.", status.HTTP_400_BAD_REQUEST)

        application.status = ApplicationStatus.ACCEPTED
        application.save(update_fields=["status"])

        return success_response(SUCCESS_MESSAGES["ACCEPTED"])


class ApplicationRejectView(APIView):
    """[REQ-APLY-005] 지원 거절"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="지원 거절",
        description="모집 공고 작성자가 지원을 거절합니다.",
        responses={200: OpenApiTypes.OBJECT},
        tags=["Application - Recruiter"],
    )
    @transaction.atomic
    def post(self, request: Request, application_id: int) -> Response:
        user = get_authenticated_user(request)

        application = get_application_with_relations(application_id)
        if application is None:
            return error_response(ERROR_MESSAGES["APPLICATION_NOT_FOUND"], status.HTTP_404_NOT_FOUND)

        if not is_recruitment_author(application.recruitment, user):
            return error_response(ERROR_MESSAGES["PERMISSION_DENIED"], status.HTTP_403_FORBIDDEN)

        if application.status != ApplicationStatus.PENDING:
            return error_response("이미 처리된 지원입니다.", status.HTTP_400_BAD_REQUEST)

        application.status = ApplicationStatus.REJECTED
        application.save(update_fields=["status"])

        return success_response(SUCCESS_MESSAGES["REJECTED"])