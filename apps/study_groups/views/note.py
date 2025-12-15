from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_groups.models import (
    GroupMember,
    StudyGroup,
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.study_groups.serializers import (
    StudyNoteCreateSerializer,
    StudyNoteDetailSerializer,
    StudyNoteListSerializer,
)


class NotePagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"


class StudyNoteAPIView(APIView):
    """노트 작성 + 목록 조회 API"""

    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotePagination

    @extend_schema(
        summary="스터디 노트 목록 조회",
        responses={
            200: OpenApiResponse(response=StudyNoteListSerializer(many=True)),
            401: OpenApiResponse(description="인증 필요"),
            403: OpenApiResponse(description="그룹 멤버만 조회 가능"),
            404: OpenApiResponse(description="스터디 그룹 없음"),
        },
    )
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


class StudyNoteDetailAPIView(APIView):
    """노트 상세 조회 및 수정 API"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, study_group_id: int, note_id: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=study_group_id)
        if not GroupMember.objects.filter(study_group_id=study_group, user_id=request.user).exists():
            return Response({"detail": "이 스터디 그룹의 멤버만 조회할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        note = get_object_or_404(
            StudyNote.objects.select_related("author").prefetch_related("images", "attachments"),
            pk=note_id,
            study_group=study_group,
        )
        serializer = StudyNoteDetailSerializer(note)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, study_group_id: int, note_id: int) -> Response:
        study_group = get_object_or_404(StudyGroup, pk=study_group_id)
        note = get_object_or_404(
            StudyNote.objects.prefetch_related("images", "attachments").select_related("author"),
            pk=note_id,
            study_group=study_group,
        )
        if note.author != request.user:
            return Response({"detail": "작성자만 수정할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = StudyNoteCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 본문 필드 업데이트
        for field in ("title", "content"):
            if field in data:
                setattr(note, field, data[field])
        note.save()

        # 첨부/이미지는 간단히 교체
        if "images" in data:
            note.images.all().delete()
            images = [StudyNoteImage(study_note=note, img_url=url) for url in data.get("images", [])]
            if images:
                StudyNoteImage.objects.bulk_create(images)

        if "attachments" in data:
            note.attachments.all().delete()
            attachment_objs = []
            for item in data.get("attachments", []):
                file_url = item.get("file_url")
                file_name = item.get("file_name")
                if file_url and file_name:
                    attachment_objs.append(
                        StudyNoteAttachment(study_note=note, file_url=file_url, file_name=file_name)
                    )
            if attachment_objs:
                StudyNoteAttachment.objects.bulk_create(attachment_objs)

        return Response(StudyNoteDetailSerializer(note).data, status=status.HTTP_200_OK)
