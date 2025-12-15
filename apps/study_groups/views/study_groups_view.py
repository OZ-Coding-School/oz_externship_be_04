from typing import Optional, cast

from django.contrib.auth.models import AnonymousUser
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
    StudyGroupListSerializer,
    StudyGroupSerializer,
)
from apps.study_groups.serializers.study_group import StudyGroupDetailSerializer
from apps.study_groups.services.study_group_service import (
    create_study_group,
    delegate_leader,
    delete_study_group,
    get_study_group_list,
    kick_member,
    leave_study_group,
    retrieve_study_group,
    update_study_group,
)
from apps.users.models import User


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
        user = request.user

        serializer = StudyGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # study_group = create_study_group(user, serializer.validated_data)
        return Response(
            {"detail": "스터디 그룹 생성에 성공하였습니다."},
            status=status.HTTP_201_CREATED,
        )


# 스터디 그룹 목록 보기
class StudyGroupListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 목록 조회",
        description="스터디 그룹 목록을 조회합니다.",
        responses=StudyGroupListSerializer,
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                description="검색어",
                required=False,
            ),
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
        search = request.query_params.get("search")
        queryset = get_study_group_list(status_filter)
        if search:  # search None 대비
            queryset = queryset.filter(name__icontains=search)

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
        study_group = retrieve_study_group(pk)
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
        study_group = update_study_group(study_group, serializer.validated_data)
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
        user = cast(User, request.user)
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

        delegate_leader(current_leader, target_member)
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
        user = cast(User, request.user)
        membership = GroupMember.objects.filter(study_group_id=study_group_id, user_id=user.id).first()
        if membership is None:
            return Response({"error_detail": "스터디 그룹을 찾을 수 없습니다."}, status=404)

        try:
            leave_study_group(membership)
        except ValueError as e:
            return Response({"error_detail": str(e)}, status=400)

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
        user = cast(User, request.user)
        current_leader = GroupMember.objects.filter(study_group_id=study_group_id, user_id=user.id).first()
        if not current_leader or not current_leader.is_leader:
            return Response({"error_detail": "리더만 멤버를 추방할 수 있습니다."}, status=403)
        # 멤버십 -> 멤버 / is None -> not (bool)
        target_member = GroupMember.objects.filter(study_group_id=study_group_id, user_id=member_id).first()
        if not target_member:
            return Response({"error_detail": "해당 멤버를 찾을 수 없습니다."}, status=404)

        try:
            kick_member(current_leader, target_member)
        except ValueError as e:
            return Response({"error_detail": str(e)}, status=400)

        return Response(status=200)
