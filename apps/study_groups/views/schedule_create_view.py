from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiExample
from django.http import Http404


from apps.study_groups.models import StudyGroup, GroupSchedule
from apps.study_groups.serializers import schedule_serializers
from apps.study_groups.serializers.schedule_serializers import (GroupScheduleSerializer)
from apps.study_groups.services.schedule_create_service import ScheduleCreateService


class ScheduleListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = schedule_serializers.GroupScheduleSerializer

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
                    "title": "스케줄 제목 예시",
                    "objective": "스케줄 설명 예시!",
                    "session_date": "2025-12-01",
                    "start_time": "10:00:00",
                    "end_time": "12:00:00"
                },
            )
        ],
    )

    def post(self, request, group_id: int):
        try:
            study_group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            raise Http404("해당 스터디 그룹을 찾을 수 없습니다.")

        data = {**request.data, "study_group": study_group.id}

        serializer = GroupScheduleSerializer(data=data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors, "error_code": "잘못된 입력입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule = ScheduleCreateService.create_schedule(serializer.validated_data)
        response_data = GroupScheduleSerializer(schedule).data

        return Response(
            {"success": True, "data": response_data}, status=status.HTTP_201_CREATED
        )

    def get(self, request, group_id: int):
        schedules = GroupSchedule.objects.filter(study_group_id=group_id)
        serializer = GroupScheduleSerializer(schedules, many=True)
        return Response({"success": True, "data": serializer.data})