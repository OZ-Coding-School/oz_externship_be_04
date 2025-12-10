from drf_spectacular.types import OpenApiTypes
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
        responses={201: GroupScheduleSerializer, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                name="스케줄 생성 예시",
                value={
                    "title": "스케줄 제목",
                    "objective": "설명",
                    "session_date": "2026-12-01",
                    "start_time": "10:00:00",
                    "end_time": "12:00:00",
                    "participants": [1, 2, 3],
                },
            )
        ],
    )
    def post(self, request: Request, group_id: int) -> Response:
        study_group = StudyGroup.objects.filter(id=group_id).first()
        if not study_group:
            return Response({"detail": "존재하지 않는 스터디 그룹입니다."}, status.HTTP_404_NOT_FOUND)
        assert request.user.pk is not None
        if not GroupMember.objects.filter(user_id=request.user.pk, study_group_id=group_id).exists():
            return Response({"detail": "요청 유저는 이 스터디의 멤버가 아닙니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = GroupScheduleSerializer(
            data=request.data,
            context={"study_group": study_group},
        )
        serializer.is_valid(raise_exception=True)

        schedule = ScheduleService.create_schedule(
            validated_data=serializer.validated_data,
            group_id=group_id,
        )

        serializer = GroupScheduleSerializer(schedule)
        return Response({"data": serializer.data}, status=status.HTTP_201_CREATED)

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
        responses={200: GroupScheduleSerializer, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
    )
    def get(self, request: Request, group_id: int, schedule_id: int) -> Response:
        schedule = ScheduleService.retrieve_schedule(schedule_id=schedule_id)
        if schedule is None:
            return Response({"detail": "존재하지 않는 스케줄입니다."}, status=status.HTTP_404_NOT_FOUND)

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
        responses={200: GroupScheduleSerializer, 401: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT},
        examples=[
            OpenApiExample(
                name="스케줄 수성 예시",
                value={
                    "title": "스케줄 제목 수정123",
                    "objective": "설명수정123",
                    "session_date": "2026-12-01",
                    "start_time": "11:00:00",
                    "end_time": "11:50:00",
                    "participants": [2, 3],
                },
            )
        ],
    )
    def put(self, request: Request, group_id: int, schedule_id: int) -> Response:
        schedule = ScheduleService.retrieve_schedule(schedule_id=schedule_id)
        if schedule is None:
            return Response({"detail": "존재하지 않는 스케줄입니다."}, status=status.HTTP_404_NOT_FOUND)

        if schedule.study_group_id != group_id:
            return Response({"detail": "접근 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = GroupScheduleSerializer(
            schedule,
            data=request.data,
            context={"study_group": schedule.study_group},
        )
        serializer.is_valid(raise_exception=True)

        ScheduleService.update_schedule(
            schedule=schedule,
            validated_data=serializer.validated_data,
        )

        serializer = GroupScheduleSerializer(schedule)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    # 스케줄 삭제
    @extend_schema(
        tags=["Schedules"],
        summary="스케줄 삭제",
        description="특정 스케줄을 삭제합니다.",
        responses={200: OpenApiTypes.OBJECT},
    )
    def delete(self, request: Request, group_id: int, schedule_id: int) -> Response:
        schedule = ScheduleService.retrieve_schedule(schedule_id=schedule_id)
        if schedule is None:
            return Response({"detail": "존재하지 않는 스케줄입니다."}, status=status.HTTP_404_NOT_FOUND)

        if schedule.study_group_id != group_id:
            return Response({"detail": "접근 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        ScheduleService.delete_schedule(schedule=schedule)
        return Response(status=status.HTTP_204_NO_CONTENT)
