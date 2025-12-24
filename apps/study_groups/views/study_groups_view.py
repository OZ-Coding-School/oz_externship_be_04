from typing import cast

from django.contrib.auth.models import AnonymousUser
from django.http import Http404
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
    MemberResponseSerializer,
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


class StudyGroupListCreateAPIView(APIView):
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
        user = cast(User, request.user)  # is_authenticated 사용하므로 user 객체 cast 처리로 진행
        queryset = get_study_group_list(user=user, status=status_filter)  # user 추가
        if search:  # search None 대비
            queryset = queryset.filter(name__icontains=search)

        serializer = StudyGroupListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="스터디 그룹 생성",
        description="스터디 그룹을 생성합니다.",
        request=StudyGroupSerializer,
        responses={201: StudyGroupSerializer, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        tags=["StudyGroup"],
    )
    def post(self, request: Request) -> Response:
        serializer = StudyGroupSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        if isinstance(request.user, AnonymousUser):
            return Response({"error_detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        study_group = create_study_group(
            user=request.user,
            validated_data=serializer.validated_data,
        )
        return Response(
            StudyGroupSerializer(study_group, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class StudyGroupRetrieveUpdateDestroyAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # 상세조회
    @extend_schema(
        summary="스터디 그룹 상세 조회",
        description="스터디 그룹 상세정보를 조회합니다.",
        responses={
            200: StudyGroupDetailSerializer,
            401: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: ErrorDetailResponseSerializer,
        },  # 404 추가
        tags=["StudyGroup"],
    )
    # 가장 직접적인 500 에러 원인 추정... url과 불일치하여 pk 대신 그룹 아이디로 통일했습니다.
    def get(self, request: Request, group_id: int) -> Response:
        # 404 예외처리
        user = cast(User, request.user)
        try:
            # 여기도 group_id로 통일
            study_group = retrieve_study_group(group_id=group_id, user=user)
        except Http404 as e:
            # 없는 그룹 / 외부인
            error_message = str(e) if str(e) else "소속된 스터디 그룹이 아닙니다."
            return Response(
                {"error_detail": error_message},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = StudyGroupDetailSerializer(study_group, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 수정
    @extend_schema(
        summary="스터디 그룹 수정",
        description="스터디 그룹 정보를 수정합니다. 리더만 수정할 수 있습니다.",
        request=StudyGroupSerializer,
        responses={200: StudyGroupSerializer, 401: OpenApiTypes.OBJECT, 403: ErrorDetailResponseSerializer},
        tags=["StudyGroup"],
    )
    def patch(self, request: Request, group_id: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=group_id)

        # 리더 권한 확인
        user = cast(User, request.user)
        is_leader = GroupMember.objects.filter(
            study_group_id=study_group.id,
            user_id=user.id,
            is_leader=True,
        ).exists()

        if not is_leader:
            return Response(
                {"error_detail": "스터디 그룹 수정 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StudyGroupSerializer(study_group, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        study_group = update_study_group(study_group, serializer.validated_data)
        return Response(
            StudyGroupSerializer(study_group, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    # 삭제
    @extend_schema(
        summary="스터디 그룹 삭제",
        description="스터디 그룹을 삭제합니다. 리더만 삭제할 수 있습니다.",
        responses={
            200: DetailResponseSerializer,
            401: ErrorDetailResponseSerializer,
            403: ErrorDetailResponseSerializer,
            404: ErrorDetailResponseSerializer,
        },
        tags=["StudyGroup"],
    )
    def delete(self, request: Request, group_id: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=group_id)

        if isinstance(request.user, AnonymousUser):
            return Response({"error_detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            delete_study_group(study_group, request.user)
        except PermissionError as e:
            return Response({"error_detail": str(e)}, status=status.HTTP_403_FORBIDDEN)

        return Response(status=status.HTTP_200_OK)


class DelegateLeaderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # 위임
    @extend_schema(
        summary="스터디 그룹 리더 위임",
        description="스터디 그룹 리더 권한을 특정 멤버에게 위임합니다.",
        request=DelegateLeaderRequestSerializer,
        responses={
            200: MemberResponseSerializer,
            401: ErrorDetailResponseSerializer,
            403: ErrorDetailResponseSerializer,
            404: ErrorDetailResponseSerializer,
        },
        tags=["StudyGroup"],
    )
    def post(self, request: Request, group_id: int) -> Response:
        serializer = DelegateLeaderRequestSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        if isinstance(request.user, AnonymousUser):
            return Response({"error_detail": "로그인이 필요합니다."}, status=401)

        # target_member_id로 GroupMember 조회
        target_member_id = serializer.validated_data["target_member_id"]
        try:
            target_member = GroupMember.objects.get(id=target_member_id, study_group_id=group_id)
        except GroupMember.DoesNotExist:
            return Response({"error_detail": "해당 멤버를 찾을 수 없습니다."}, status=404)

        user = cast(User, request.user)
        try:
            delegate_leader(
                group_id=group_id,
                current_user=user,
                target_user_id=target_member.user_id.id,
            )
        except PermissionError as e:
            return Response({"error_detail": str(e)}, status=403)
        except ValueError as e:
            return Response({"error_detail": str(e)}, status=404)

        return Response(
            {"member_id": target_member.id, "detail": "리더 권한이 위임되었습니다."},
            status=200,
        )


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
    def delete(self, request: Request, group_id: int) -> Response:
        if isinstance(request.user, AnonymousUser):
            return Response({"error_detail": "로그인이 필요합니다."}, status=401)

        user = cast(User, request.user)
        try:
            leave_study_group(
                group_id=group_id,
                user=user,
            )
        except ValueError as e:
            return Response({"error_detail": str(e)}, status=400)

        return Response({"detail": "스터디 그룹에서 나가기에 성공했습니다."}, status=status.HTTP_200_OK)


class KickStudyGroupMemberAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="스터디 그룹 멤버 추방",
        description="리더가 스터디 그룹의 특정 멤버를 추방합니다.",
        responses={
            200: MemberResponseSerializer,
            400: ErrorDetailResponseSerializer,
            401: ErrorDetailResponseSerializer,
            403: ErrorDetailResponseSerializer,
            404: ErrorDetailResponseSerializer,
        },
        tags=["StudyGroup"],
    )
    def delete(self, request: Request, group_id: int, member_id: int) -> Response:
        if isinstance(request.user, AnonymousUser):
            return Response({"error_detail": "로그인이 필요합니다."}, status=401)

        # member_id로 GroupMember 조회 (삭제 전)
        try:
            target_member = GroupMember.objects.get(id=member_id, study_group_id=group_id)
        except GroupMember.DoesNotExist:
            return Response({"error_detail": "해당 멤버를 찾을 수 없습니다."}, status=404)

        user = cast(User, request.user)
        try:
            kick_member(
                group_id=group_id,
                current_user=user,
                target_user_id=target_member.user_id.id,
            )
        except PermissionError as e:
            return Response({"error_detail": str(e)}, status=403)
        except ValueError as e:
            return Response({"error_detail": str(e)}, status=404)

        return Response(
            {"member_id": target_member.id, "detail": "스터디 그룹에서 멤버를 추방하는데 성공했습니다."},
            status=status.HTTP_200_OK,
        )
