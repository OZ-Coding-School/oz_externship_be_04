from typing import Any, cast

from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_groups.models import GroupMember, Review, StudyGroup
from apps.study_groups.serializers.review_serializer import (
    ReviewCreateSerializer,
    ReviewListSerializer,
    ReviewSerializer,
    ReviewUpdateSerializer,
)
from apps.users.models import User


class StudyGroupReviewBaseAPIView(APIView):
    def _error(self, message: str, http_status: int) -> Response:
        return Response({"error_detail": message}, status=http_status)

    def _has_permission_to_review(self, user: Any, study_group: StudyGroup) -> bool:
        return GroupMember.objects.filter(
            study_group_id=study_group,
            user_id=user,
        ).exists()

    def _auth_and_get_group_or_response(
        self, request: Request, group_id: int
    ) -> tuple[StudyGroup | None, Response | None]:
        # 인증여부 확인
        if not request.user.is_authenticated:
            return None, self._error(
                "자격 인증 데이터가 제공되지 않았습니다.",
                status.HTTP_401_UNAUTHORIZED,
            )

        # 스터디 그룹 존재여부 확인
        try:
            study_group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            return None, self._error(
                "스터디 그룹을 찾을 수 없습니다.",
                status.HTTP_404_NOT_FOUND,
            )

        # 스터디 그룹 참여여부 확인
        if not self._has_permission_to_review(request.user, study_group):
            return None, self._error(
                "소속된 스터디 그룹이 아닙니다.",
                status.HTTP_403_FORBIDDEN,
            )

        return study_group, None


class StudyGroupReviewCreateAPIView(StudyGroupReviewBaseAPIView):
    @extend_schema(
        summary="스터디 그룹 리뷰 생성",
        tags=["StudyGroup"],
    )
    def post(self, request: Request, group_id: int) -> Response:
        try:
            study_group, error_response = self._auth_and_get_group_or_response(request, group_id)
            if error_response:
                return error_response

            serializer = ReviewCreateSerializer(
                data=request.data,
                context={
                    "request": request,
                    "study_group": study_group,
                },
            )

            if not serializer.is_valid():
                return Response(
                    {"error_detail": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 리뷰 생성
            try:
                serializer.save()
                # 이미 리뷰를 작성한 경우
            except IntegrityError:
                return Response(
                    {"error_detail": {"non_field_errors": ["이미 이 스터디 그룹에 대한 리뷰를 작성했습니다."]}},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {"detail": "스터디 리뷰 작성에 성공했습니다."},
                status=status.HTTP_200_OK,
            )

        except PermissionDenied:
            return Response(
                {"error_detail": "권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            # 공통 500 에러
            return Response(
                {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="스터디 그룹 리뷰 목록 조회",
        tags=["StudyGroup"],
    )
    def get(self, request: Request, group_id: int) -> Response:
        try:
            study_group, error_response = self._auth_and_get_group_or_response(request, group_id)
            if error_response:
                return error_response

            # 해당 스터디 그룹의 리뷰 목록 조회
            reviews = Review.objects.filter(study_group=study_group).order_by("-created_at")
            serializer = ReviewListSerializer(
                cast(Any, reviews),
                many=True,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except PermissionDenied:
            return Response(
                {"error_detail": "권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            return Response(
                {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StudyGroupReviewUpdateAPIView(StudyGroupReviewBaseAPIView):
    @extend_schema(
        summary="스터디 그룹 리뷰 수정",
        tags=["StudyGroup"],
    )
    def patch(self, request: Request, group_id: int, review_id: int) -> Response:
        try:
            study_group, error_response = self._auth_and_get_group_or_response(request, group_id)
            if error_response:
                return error_response

            # 리뷰 존재 여부 확인
            try:
                review = Review.objects.get(id=review_id, study_group=study_group)
            except Review.DoesNotExist:
                return Response(
                    {"error_detail": "스터디 리뷰를 찾을 수 없습니다."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 5) 작성자 본인인지 확인
            if review.user != request.user:
                return Response(
                    {"error_detail": "권한이 없습니다."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # 데이터 검증
            serializer = ReviewUpdateSerializer(instance=review, data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"error_detail": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 수정 반영
            serializer.save()  # 내부에서 update 호출

            # 성공 응답
            return Response(serializer.data, status=status.HTTP_200_OK)

        except PermissionDenied:
            return Response(
                {"error_detail": "권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception:
            return Response(
                {"error_detail": "서버에서 알 수 없는 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
