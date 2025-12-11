from typing import Optional

from django.contrib.auth.models import AnonymousUser
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_groups.models import GroupMember, StudyGroup
from apps.study_groups.serializers import (
    DelegateLeaderRequestSerializer,
    DetailResponseSerializer,
    ErrorDetailResponseSerializer,
)
from apps.study_groups.serializers.study_group import (
    StudyGroupDetailSerializer,
    StudyGroupListSerializer,
    StudyGroupSerializer,
)
from apps.users.models import User as CustomUser


def get_authenticated_user(request: Request) -> Optional[CustomUser]:
    user = request.user
    if isinstance(user, AnonymousUser):
        return None
    return user


# 스터디 그룹 만들기
class StudyGroupCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 생성",
        description="스터디 그룹을 생성합니다.",
        request=StudyGroupSerializer,
        responses={201: StudyGroupSerializer, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        tags=["StudyGroup"],
    )
    def post(self, request: Request) -> Response:
        user = get_authenticated_user(request)
        if user is None:
            return Response(
                {"error_detail": "인증 정보가 올바르지 않습니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        serializer = StudyGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        study_group = serializer.save()

        GroupMember.objects.create(
            study_group_id=study_group,
            user_id=user,
            is_leader=True,
        )
        return Response(StudyGroupSerializer(study_group).data, status=status.HTTP_201_CREATED)


# 스터디 그룹 목록 보기
class StudyGroupListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 목록 조회",
        description="스터디 그룹 목록을 조회합니다.",
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
        tags=["StudyGroup"],
    )
    def get(self, request: Request) -> Response:
        status_filter = request.query_params.get("status")
        queryset: QuerySet[StudyGroup] = StudyGroup.objects.all()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        serializer = StudyGroupListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


# 스터디 그룹 상세정보 조회
class StudyGroupRetrieveAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 상세 조회",
        description="스터디 그룹 상세정보를 조회합니다.",
        responses={200: StudyGroupDetailSerializer, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        tags=["StudyGroup"],
    )
    def get(self, request: Request, pk: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=pk)
        serializer = StudyGroupDetailSerializer(study_group, context={"request": request})
        return Response(serializer.data)


# 스터디 그룹 수정(업데이트)하기
# 로직 실행 전에 멤버/리더 여부 확인 필요
class StudyGroupUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 수정",
        description="스터디 그룹 정보를 수정합니다.",
        request=StudyGroupSerializer,
        responses={200: StudyGroupSerializer, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        tags=["StudyGroup"],
    )
    def patch(self, request: Request, pk: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=pk)
        serializer = StudyGroupSerializer(study_group, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        study_group = serializer.save()
        return Response(StudyGroupSerializer(study_group).data)


# 스터디그룹 삭제하기
# 로직 실행 전에 멤버/리더 여부 확인 필요
class StudyGroupDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 삭제",
        description="스터디 그룹을 삭제합니다.",
        # 삭제 API이므로, 굳이 응답 주지 않아도 됨! -> 204: None으로 처리가 더 RESTFUL
        responses={204: None},
        tags=["StudyGroup"],
    )
    def delete(self, request: Request, pk: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=pk)
        study_group.delete()
        # 204 -> 삭제이므로 별도 디테일한 응답 필요x NO_CONTENT
        return Response(status=status.HTTP_204_NO_CONTENT)


# 리더 위임
class DelegateLeaderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 리더 위임",
        description="스터디 그룹 리더 권한을 특정 멤버에게 위임합니다.",
        request=DelegateLeaderRequestSerializer,
        responses={
            200: DetailResponseSerializer,
            401: ErrorDetailResponseSerializer,
            403: ErrorDetailResponseSerializer,
            404: ErrorDetailResponseSerializer,
        },
        tags=["StudyGroup"],
    )
    def post(self, request: Request, study_group_id: int) -> Response:
        user = get_authenticated_user(request)
        if user is None:
            return Response({"error_detail": "인증 정보가 올바르지 않습니다."}, status=401)

        current_leader = GroupMember.objects.filter(
            study_group_id=study_group_id,
            user_id=user.pk,
            is_leader=True,
        ).first()

        if current_leader is None:
            return Response({"error_detail": "권한이 없습니다."}, status=403)

        serializer = DelegateLeaderRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_member_id = serializer.validated_data["target_member_id"]

        target_member = GroupMember.objects.filter(
            study_group_id=study_group_id,
            user_id=target_member_id,
        ).first()

        if target_member is None:
            return Response({"error_detail": "해당 멤버를 찾을 수 없습니다."}, status=404)

        current_leader.is_leader = False
        current_leader.save(update_fields=["is_leader"])

        target_member.is_leader = True
        target_member.save(update_fields=["is_leader"])

        return Response({"detail": "리더 권한이 위임되었습니다."}, status=200)


# 스터디 그룹 나가기
class LeaveStudyGroupMeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 나가기",
        description="본인이 속한 스터디 그룹에서 나갑니다. 리더는 나갈 수 없습니다.",
        responses={
            200: DetailResponseSerializer,
            400: ErrorDetailResponseSerializer,
            401: ErrorDetailResponseSerializer,
            404: ErrorDetailResponseSerializer,
        },
        tags=["StudyGroup"],
    )
    def delete(self, request: Request, study_group_id: int) -> Response:
        user = get_authenticated_user(request)
        if user is None:
            return Response({"error_detail": "인증 정보가 올바르지 않습니다."}, status=401)

        membership = GroupMember.objects.filter(study_group_id=study_group_id, user_id=user.id).first()
        if membership is None:
            return Response({"error_detail": "스터디 그룹을 찾을 수 없습니다."}, status=404)

        if membership.is_leader:
            return Response({"error_detail": "리더는 스터디 그룹을 나갈 수 없습니다."}, status=400)

        membership.delete()
        return Response(status=200)


# 멤버 추방
class KickStudyGroupMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 멤버 추방",
        description="리더가 스터디 그룹의 특정 멤버를 추방합니다.",
        responses={
            200: DetailResponseSerializer,
            400: ErrorDetailResponseSerializer,
            401: ErrorDetailResponseSerializer,
            403: ErrorDetailResponseSerializer,
            404: ErrorDetailResponseSerializer,
        },
        tags=["StudyGroup"],
    )
    def delete(self, request: Request, study_group_id: int, member_id: int) -> Response:
        member = get_authenticated_user(request)
        if member is None:
            return Response({"error_detail": "인증 정보가 올바르지 않습니다."}, status=401)

        current_membership = GroupMember.objects.filter(study_group_id=study_group_id, user_id=member.id).first()
        if current_membership is None:
            return Response({"error_detail": "리더만 멤버를 추방할 수 있습니다."}, status=403)
        if not current_membership.is_leader:
            return Response({"error_detail": "리더만 멤버를 추방할 수 있습니다."}, status=403)

        target_membership = GroupMember.objects.filter(study_group_id=study_group_id, user_id=member_id).first()
        if target_membership is None:
            return Response({"error_detail": "해당 멤버를 찾을 수 없습니다."}, status=404)

        if target_membership.is_leader:
            return Response({"error_detail": "리더는 추방할 수 없습니다."}, status=400)

        target_membership.delete()
        return Response(status=200)
