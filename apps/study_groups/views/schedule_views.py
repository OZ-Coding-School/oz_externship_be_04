from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
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
        tags=["StudyGroups"],
        summary="스케줄 생성",
        description="스터디 그룹에 새로운 스케줄을 생성합니다.",
        request=GroupScheduleSerializer,
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
        responses={
            201: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="생성 성공",
                examples=[
                    OpenApiExample(
                        name="201 응답 예시",
                        value={"detail": "스터디 스케줄 생성에 성공했습니다."},
                        status_codes=["201"],
                    )
                ],
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="잘못된 요청",
                examples=[
                    OpenApiExample(
                        name="400 예시",
                        value={"error_detail": {"start_date": ["이 필드는 필수항목입니다."]}},
                        status_codes=["400"],
                    )
                ],
            ),
            401: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="인증 실패",
                examples=[
                    OpenApiExample(
                        name="401 예시",
                        value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                        status_codes=["401"],
                    )
                ],
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="권한 없음",
                examples=[
                    OpenApiExample(
                        name="403 예시",
                        value={"error_detail": "권한이 없습니다."},
                        status_codes=["403"],
                    )
                ],
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="리소스를 찾을 수 없음",
                examples=[
                    OpenApiExample(
                        name="404 예시",
                        value={"error_detail": "스터디 그룹을 찾을 수 없습니다."},
                        status_codes=["404"],
                    )
                ],
            ),
        },
    )
    def post(self, request: Request, group_id: int) -> Response:
        study_group = StudyGroup.objects.filter(id=group_id).first()
        if not study_group:
            return Response({"error_detail": "스터디 그룹을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        assert request.user.pk is not None
        if not GroupMember.objects.filter(user_id=request.user.pk, study_group_id=group_id).exists():
            return Response({"error_detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

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
        return Response({"detail": "스터디 스케줄 생성에 성공했습니다."}, status=status.HTTP_201_CREATED)

    # 스케줄 조회
    @extend_schema(
        tags=["StudyGroups"],
        summary="스케줄 목록 조회",
        description="스터디 그룹의 전체 스케줄 목록을 조회합니다.",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="요청 성공",
                examples=[
                    OpenApiExample(
                        name="200 예시",
                        value={
                            "id": 1,
                            "title": "파이썬 스터디 1회차",
                            "session_date": "2025-11-20",
                            "start_time": "10:00",
                            "end_time": "11:00",
                        },
                        status_codes=["200"],
                    )
                ],
            ),
            401: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="인증 실패",
                examples=[
                    OpenApiExample(
                        name="401 예시",
                        value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                        status_codes=["401"],
                    )
                ],
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="권한 없음",
                examples=[
                    OpenApiExample(
                        name="403 예시",
                        value={"error_detail": "권한이 없습니다."},
                        status_codes=["403"],
                    )
                ],
            ),
        },
    )
    def get(self, request: Request, group_id: int) -> Response:
        schedules = ScheduleService.list_schedules(group_id=group_id)
        serializer = GroupScheduleSerializer(schedules, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ScheduleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # 스케줄 상세조회
    @extend_schema(
        tags=["StudyGroups"],
        summary="스케줄 상세 조회",
        description="특정 스케줄의 상세 정보를 조회합니다.",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="요청 성공",
                examples=[
                    OpenApiExample(
                        name="200 예시",
                        value={
                            "id": 1,
                            "group_id": 1,
                            "title": "파이썬 스터디 1회차",
                            "objective": "파이썬 자료형 마스터하기",
                            "session_date": "2025-11-20",
                            "start_time": "10:00",
                            "end_time": "11:00",
                            "participants": [
                                {
                                    "id": 1,
                                    "nickname": "testuser",
                                    "is_leader": True,
                                    "profile_img_url": "https://example.com/images/users/profiles/image.png",
                                }
                            ],
                        },
                        status_codes=["200"],
                    )
                ],
            ),
            401: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="인증 실패",
                examples=[
                    OpenApiExample(
                        name="401 예시",
                        value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                        status_codes=["401"],
                    )
                ],
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="권한 없음",
                examples=[
                    OpenApiExample(
                        name="403 예시",
                        value={"error_detail": "권한이 없습니다."},
                        status_codes=["403"],
                    )
                ],
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="리소스를 찾을 수 없음",
                examples=[
                    OpenApiExample(
                        name="404 예시",
                        value={"error_detail": "스터디 그룹을 찾을 수 없습니다."},
                        status_codes=["404"],
                    )
                ],
            ),
        },
    )
    def get(self, request: Request, group_id: int, schedule_id: int) -> Response:
        schedule = ScheduleService.retrieve_schedule(schedule_id=schedule_id)
        if schedule is None:
            return Response({"error_detail": "스터디 스케줄을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if schedule.study_group_id != group_id:
            return Response({"error_detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = GroupScheduleSerializer(schedule)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 스케줄 수정
    @extend_schema(
        tags=["StudyGroups"],
        summary="스케줄 수정",
        description="기존 스케줄의 정보를 수정합니다.",
        request=GroupScheduleSerializer,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="요청 성공",
                examples=[
                    OpenApiExample(
                        name="200 예시",
                        value={
                            "id": 1,
                            "group_id": 1,
                            "title": "파이썬 스터디 2회차",
                            "objective": "파이썬 자료형 마스터하기",
                            "session_date": "2025-11-20",
                            "start_time": "10:00",
                            "end_time": "11:00",
                            "participants": [
                                {
                                    "id": 3,
                                    "nickname": "testuser3",
                                    "is_leader": True,
                                    "profile_img_url": "https://example.com/images/users/profiles/image.png",
                                }
                            ],
                        },
                        status_codes=["200"],
                    )
                ],
            ),
            400: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="잘못된 요청",
                examples=[
                    OpenApiExample(
                        name="400 예시",
                        value={"error_detail": {"start_date": ["이 필드는 필수항목입니다."]}},
                        status_codes=["400"],
                    )
                ],
            ),
            401: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="인증 실패",
                examples=[
                    OpenApiExample(
                        name="401 예시",
                        value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                        status_codes=["401"],
                    )
                ],
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="권한 없음",
                examples=[
                    OpenApiExample(
                        name="403 예시",
                        value={"error_detail": "권한이 없습니다."},
                        status_codes=["403"],
                    )
                ],
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="리소스를 찾을 수 없음",
                examples=[
                    OpenApiExample(
                        name="404 예시",
                        value={"error_detail": "스터디 스케줄을 찾을 수 없습니다."},
                        status_codes=["404"],
                    )
                ],
            ),
        },
        examples=[
            OpenApiExample(
                name="스케줄 수정 예시",
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
            return Response({"error_detail": "스터디 스케줄을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if schedule.study_group_id != group_id:
            return Response({"error_detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

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
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 스케줄 삭제
    @extend_schema(
        tags=["StudyGroups"],
        summary="스케줄 삭제",
        description="특정 스케줄을 삭제합니다.",
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="요청 성공",
                examples=[
                    OpenApiExample(
                        name="200 예시",
                        value={"detail": "스터디 스케줄 삭제에 성공했습니다."},
                        status_codes=["200"],
                    )
                ],
            ),
            401: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="인증 실패",
                examples=[
                    OpenApiExample(
                        name="401 예시",
                        value={"error_detail": "자격 인증 데이터가 제공되지 않았습니다."},
                        status_codes=["401"],
                    )
                ],
            ),
            403: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="권한 없음",
                examples=[
                    OpenApiExample(
                        name="403 예시",
                        value={"error_detail": "권한이 없습니다."},
                        status_codes=["403"],
                    )
                ],
            ),
            404: OpenApiResponse(
                response=OpenApiTypes.STR,
                description="리소스를 찾을 수 없음",
                examples=[
                    OpenApiExample(
                        name="404 예시",
                        value={"error_detail": "스터디 그룹을 찾을 수 없습니다."},
                        status_codes=["404"],
                    ),
                    OpenApiExample(
                        name="404 예시",
                        value={"error_detail": "스터디 스케줄을 찾을 수 없습니다."},
                        status_codes=["404"],
                    ),
                ],
            ),
        },
    )
    def delete(self, request: Request, group_id: int, schedule_id: int) -> Response:
        schedule = ScheduleService.retrieve_schedule(schedule_id=schedule_id)
        if schedule is None:
            return Response({"error_detail": "스터디 스케줄을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if schedule.study_group_id != group_id:
            return Response({"error_detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        ScheduleService.delete_schedule(schedule=schedule)
        return Response({"detail": "스터디 스케줄 삭제에 성공했습니다."}, status=status.HTTP_200_OK)
