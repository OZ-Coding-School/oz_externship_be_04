from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_groups.models import GroupMember, StudyNote, StudyGroup
from apps.study_groups.serializers import StudyNoteCreateSerializer, StudyNoteListSerializer


class StudyNotePagination(PageNumberPagination):
    page_size = 5


class StudyNoteCreateAPIView(APIView):
    """노트 작성/목록 API (간단 버전)"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        study_group_id = kwargs.get("study_group_id")
        study_group = StudyGroup.objects.filter(id=study_group_id).first()
        if not study_group:
            return Response({"detail": "존재하지 않는 스터디 그룹입니다."}, status=status.HTTP_404_NOT_FOUND)

        is_member = GroupMember.objects.filter(study_group=study_group, user=request.user).exists()
        if not is_member:
            return Response({"detail": "스터디 그룹에 소속된 멤버만 작성할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        notes = (
            StudyNote.objects.filter(study_group=study_group)
            .select_related("author")
            .prefetch_related("images")
            .order_by("-created_at")
        )

        paginator = StudyNotePagination()
        page = paginator.paginate_queryset(notes, request, view=self)

        results = []
        for note in page:
            first_image = note.images.first()
            results.append(
                {
                    "id": note.id,
                    "title": note.title,
                    "author_nickname": getattr(note.author, "nickname", ""),
                    "author_profile_img": getattr(note.author, "profile_img_url", None),
                    "created_at": note.created_at.strftime("%Y-%m-%d %H:%M"),
                    "thumbnail": first_image.img_url if first_image else None,
                }
            )

        serializer = StudyNoteListSerializer(results, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, *args, **kwargs):
        study_group_id = kwargs.get("study_group_id")
        study_group = StudyGroup.objects.filter(id=study_group_id).first()
        if not study_group:
            return Response({"detail": "존재하지 않는 스터디 그룹입니다."}, status=status.HTTP_404_NOT_FOUND)

        is_member = GroupMember.objects.filter(study_group=study_group, user=request.user).exists()
        if not is_member:
            return Response({"detail": "스터디 그룹에 소속된 멤버만 작성할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = StudyNoteCreateSerializer(
            data=request.data,
            context={"author": request.user, "study_group": study_group},
        )
        serializer.is_valid(raise_exception=True)
        note = serializer.save()
        response_data = {
            "id": note.id,
            "study_group_id": study_group.id,
            "author_id": request.user.id,
            "title": note.title,
            "content": note.content,
            "ai_summary": note.ai_summary,
            "created_at": note.created_at,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
