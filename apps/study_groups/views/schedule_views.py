from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_groups.models import StudyGroup
from apps.study_groups.serializers.schedule_serializers import GroupScheduleSerializer
from apps.study_groups.services.schedule_services import ScheduleService


class ScheduleCreateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = GroupScheduleSerializer

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
                    "session_date": "2025-12-01",
                    "start_time": "10:00:00",
                    "end_time": "12:00:00",
                    "participants": [1, 2, 3],
                },
            )
        ],
    )
    def post(self, request, group_id: int) -> Response:
        try:
            study_group = StudyGroup.objects.get(id=group_id)
        except StudyGroup.DoesNotExist:
            return Response({"success": False, "error": "스터디 그룹을 찾을 수 없습니다."}, status=404)

        data = {**request.data, "study_group": study_group.id}

        serializer = GroupScheduleSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        print("validated_data:", serializer.validated_data)

        schedule = ScheduleService.create_schedule(serializer.validated_data)
        return Response({"success": True, "data": GroupScheduleSerializer(schedule).data}, status=201)

