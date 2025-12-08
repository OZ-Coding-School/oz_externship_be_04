# schedule_views

from typing import cast

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_groups.models import GroupMember, StudyGroup
from apps.study_groups.serializers.schedule_serializers import GroupScheduleSerializer
from apps.study_groups.services.schedule_services import ScheduleService


class ScheduleView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupScheduleSerializer

    # 스케줄 생성
    @extend_schema(
        tags=["Schedules"],
        summary="스케줄 생성",
        description="스터디 그룹에 새로운 스케줄을 생성합니다.",
        request=GroupScheduleSerializer,
        responses={201: GroupScheduleSerializer},
        examples=[
            OpenApiExample(
                name="스케줄 생성 예시",
                value={
                    "title": "스케줄 제목",
                    "objective": "설명",
                    "session_date": "2025-12-01T10:00:00",
                    "start_time": "10:00:00",
                    "end_time": "12:00:00",
                    "participants": [1, 2, 3],
                },
            )
        ],
    )
    def post(self, request: Request, group_id: int) -> Response:
        study_group = StudyGroup.objects.get(id=group_id)

        serializer = GroupScheduleSerializer(
            data={
                "title": request.data["title"],
                "objective": request.data.get("objective"),
                "session_date": request.data["session_date"],
                "start_time": request.data["start_time"],
                "end_time": request.data["end_time"],
                "participants": request.data.get("participants", []),
            },
            context={"study_group": study_group},
        )
        serializer.is_valid(raise_exception=True)

        user_id = cast(int, request.user.id)
        try:
            assert request.user.pk is not None
            GroupMember.objects.get(
                user_id=request.user.pk,
                study_group_id=study_group,
            )
        except GroupMember.DoesNotExist:
            from rest_framework.exceptions import (
                ValidationError,
            )

            raise ValidationError({"detail": "요청 유저는 이 스터디의 멤버가 아닙니다."})

        participants = serializer.validated_data.get("participants", [])

        validated_data = serializer.validated_data.copy()
        validated_data["participants"] = participants

        schedule = ScheduleService.create_schedule(
            validated_data=validated_data,
            group_id=group_id,
        )

        return Response(
            {"data": GroupScheduleSerializer(schedule).data},
            status=status.HTTP_201_CREATED,
        )

    # 스케줄 조회
    @extend_schema(
        tags=["Schedules"],
        summary="스케줄 목록 조회",
        description="스터디 그룹의 전체 스케줄 목록을 조회합니다.",
        responses={200: GroupScheduleSerializer},
    )
    def get(self, request: Request, group_id: int) -> Response:
        schedules = ScheduleService.list_schedules(group_id=group_id)
        serializer = GroupScheduleSerializer(schedules, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


class ScheduleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # 스케줄 상세조회
    @extend_schema(
        tags=["Schedules"],
        summary="스케줄 상세 조회",
        description="특정 스케줄의 상세 정보를 조회합니다.",
        responses={200: GroupScheduleSerializer},
    )
    def get(self, request: Request, group_id: int, schedule_id: int) -> Response:
        schedule = ScheduleService.retrieve_schedule(schedule_id=schedule_id)

        if schedule.study_group_id != group_id:
            return Response({"detail": "접근 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = GroupScheduleSerializer(schedule)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    # 스케줄 수정
    @extend_schema(
        tags=["Schedules"],
        summary="스케줄 수정",
        description="기존 스케줄의 정보를 수정합니다.",
        request=GroupScheduleSerializer,
        responses={200: GroupScheduleSerializer},
        examples=[
            OpenApiExample(
                name="스케줄 수성 예시",
                value={
                    "title": "스케줄 제목 수정123",
                    "objective": "설명수정123",
                    "session_date": "2026-12-01T10:00:00",
                    "start_time": "11:00:00",
                    "end_time": "11:50:00",
                    "participants": [2, 3],
                },
            )
        ],
    )
    def put(self, request: Request, group_id: int, schedule_id: int) -> Response:
        schedule = ScheduleService.retrieve_schedule(schedule_id=schedule_id)

        if schedule.study_group_id != group_id:
            return Response({"detail": "접근 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        data = {
            "title": request.data["title"],
            "objective": request.data.get("objective"),
            "session_date": request.data["session_date"],
            "start_time": request.data["start_time"],
            "end_time": request.data["end_time"],
            "participants": request.data.get("participants", []),
        }

        serializer = GroupScheduleSerializer(
            schedule,
            data=data,
            context={"study_group": schedule.study_group},
        )
        serializer.is_valid(raise_exception=True)

        updated_schedule = ScheduleService.update_schedule(
            schedule=schedule,
            validated_data=serializer.validated_data,
        )

        return Response(
            {"data": GroupScheduleSerializer(updated_schedule).data},
            status=status.HTTP_200_OK,
        )

    # 스케줄 삭제
    @extend_schema(
        tags=["Schedules"],
        summary="스케줄 삭제",
        description="특정 스케줄을 삭제합니다.",
        responses={204: None},
    )
    def delete(self, request: Request, group_id: int, schedule_id: int) -> Response:
        schedule = ScheduleService.retrieve_schedule(schedule_id=schedule_id)

        if schedule.study_group_id != group_id:
            return Response({"detail": "접근 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        ScheduleService.delete_schedule(schedule=schedule)
        return Response(status=status.HTTP_204_NO_CONTENT)
