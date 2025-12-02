from apps.study_groups.serializers.schedule_serializers import GroupScheduleSerializer
from apps.study_groups.serializers.schedule_serializers import ScheduleParticipantsSerializer
from apps.study_groups.services.schedule_create_service import ScheduleCreateService
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response



class ScheduleCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        schedule_serializer = GroupScheduleSerializer(data=request.data, context={"request": request})
        schedule_serializer.is_valid(raise_exception=True)

        schedule = ScheduleCreateService.create_schedule(schedule_serializer.validated_data)

        participants_data = request.data.get("participants", [])
        for participant in participants_data:
            participant_serializer = ScheduleParticipantsSerializer(data={
                "group_schedule": schedule.id,
                "group_member": participant["group_member"],
            })
            participant_serializer.is_valid(raise_exception=True)
            participant_serializer.save()

        return Response(GroupScheduleSerializer(schedule, context={"request": request}).data, status=status.HTTP_201_CREATED)

