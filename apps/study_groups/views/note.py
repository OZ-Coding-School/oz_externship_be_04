from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_groups.models import GroupMember, StudyGroup, StudyNote
from apps.study_groups.serializers import (
    StudyNoteCreateSerializer,
    StudyNoteListSerializer,
)


class NotePagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"


class StudyNoteAPIView(APIView):
    """노트 작성 + 목록 조회 API"""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotePagination

    def get(self, request, study_group_id: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=study_group_id)
        if not GroupMember.objects.filter(study_group_id=study_group, user_id=request.user).exists():
            return Response({"detail": "이 스터디 그룹의 멤버만 조회할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        queryset = (
            StudyNote.objects.filter(study_group=study_group)
            .select_related("author")
            .prefetch_related("images")
            .order_by("-created_at", "-id")
        )
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = StudyNoteListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, study_group_id: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=study_group_id)
        if not GroupMember.objects.filter(study_group_id=study_group, user_id=request.user).exists():
            return Response({"detail": "이 스터디 그룹의 멤버만 작성할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        # 중복 검사나 복잡한 로직 없이 바로 저장
        serializer = StudyNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save(author=request.user, study_group=study_group)

        return Response(
            {
                "id": note.id,
                "study_group_id": note.study_group_id,
                "author_id": note.author_id,
                "title": note.title,
                "content": note.content,
                "ai_summary": note.ai_summary,
                "created_at": note.created_at,
            },
            status=status.HTTP_201_CREATED,
        )
