from typing import cast

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.study_groups.models import (
    StudyGroup,
    StudyNote,
    StudyNoteAttachment,
    StudyNoteImage,
)
from apps.study_groups.serializers.study_note import (
    StudyNoteCreateSerializer,
    StudyNoteDetailSerializer,
    StudyNoteListSerializer,
    StudyNoteUpdateResponseSerializer,
    StudyNoteUpdateSerializer,
)
from apps.study_groups.services.note_ai import StudyNoteAIService
from apps.users.models import User


class StudyNotePagination(PageNumberPagination):
    """스터디 노트 페이지네이션"""

    page_size = 10
    page_size_query_param = "page_size"


class StudyNoteListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StudyNotePagination

    def _create_images(self, note: StudyNote, image_urls: list[str]) -> None:
        """이미지 생성"""
        if image_urls:
            StudyNoteImage.objects.bulk_create([StudyNoteImage(study_note=note, img_url=url) for url in image_urls])

    def _create_attachments(self, note: StudyNote, files: list[dict[str, str]]) -> None:
        """첨부파일 생성"""
        if files:
            StudyNoteAttachment.objects.bulk_create(
                [StudyNoteAttachment(study_note=note, file_name=f["file_name"], file_url=f["file_url"]) for f in files]
            )

    @extend_schema(
        summary="스터디 노트 목록 조회",
        tags=["StudyGroup"],
        parameters=[
            OpenApiParameter("page", int, required=False, description="페이지 번호 (기본값: 1)"),
            OpenApiParameter("page_size", int, required=False, description="페이지 크기 (기본값: 10)"),
        ],
        responses={
            200: inline_serializer(
                name="StudyNoteListResponse",
                fields={
                    "count": serializers.IntegerField(),
                    "next": serializers.URLField(allow_null=True),
                    "previous": serializers.URLField(allow_null=True),
                    "results": StudyNoteListSerializer(many=True),
                },
            )
        },
    )
    def get(self, request: Request, group_id: int) -> Response:
        get_object_or_404(StudyGroup, id=group_id)

        notes = (
            StudyNote.objects.filter(study_group_id=group_id).select_related("author").order_by("-created_at", "-id")
        )

        paginator = self.pagination_class()
        paginated_notes = paginator.paginate_queryset(notes, request)
        serializer = StudyNoteListSerializer(paginated_notes, many=True)
        return paginator.get_paginated_response(serializer.data)

    @extend_schema(
        summary="스터디 노트 작성",
        tags=["StudyGroup"],
        request=StudyNoteCreateSerializer,
        responses={200: inline_serializer(name="StudyNoteCreateResponse", fields={"detail": serializers.CharField()})},
    )
    @transaction.atomic
    def post(self, request: Request, group_id: int) -> Response:
        group = get_object_or_404(StudyGroup, id=group_id)

        serializer = StudyNoteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        images = validated_data.pop("images", [])
        files = validated_data.pop("files", [])

        try:
            note = StudyNote.objects.create(
                study_group=group,
                author=cast(User, request.user),
                title=validated_data["title"],
                content=validated_data["content"],
            )

            self._create_images(note, images)
            self._create_attachments(note, files)

            StudyNoteAIService.summarize(note)

        except IntegrityError:
            raise ValidationError({"error_detail": "이미 사용된 파일의 url 입니다."})

        return Response({"detail": "스터디 학습 기록 작성에 성공했습니다."}, status=status.HTTP_200_OK)


class StudyNoteDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_note(self, group_id: int, note_id: int, prefetch: list[str] | None = None) -> StudyNote:
        """노트 조회 (그룹 존재 여부도 확인)"""
        get_object_or_404(StudyGroup, id=group_id)

        queryset = StudyNote.objects.select_related("author")
        if prefetch:
            queryset = queryset.prefetch_related(*prefetch)

        return get_object_or_404(queryset, id=note_id, study_group_id=group_id)

    def _check_permission(self, note: StudyNote, user: User) -> None:
        """작성자 권한 확인"""
        if note.author != user:
            raise PermissionDenied("권한이 없습니다.")

    def _update_images(self, note: StudyNote, image_urls: list[str]) -> None:
        """이미지 업데이트 (기존 삭제 후 재생성)"""
        note.images.all().delete()
        if image_urls:
            StudyNoteImage.objects.bulk_create([StudyNoteImage(study_note=note, img_url=url) for url in image_urls])

    def _update_attachments(self, note: StudyNote, files: list[dict[str, str]]) -> None:
        """첨부파일 업데이트 (기존 삭제 후 재생성)"""
        note.attachments.all().delete()
        if files:
            try:
                StudyNoteAttachment.objects.bulk_create(
                    [
                        StudyNoteAttachment(study_note=note, file_name=f["file_name"], file_url=f["file_url"])
                        for f in files
                    ]
                )
            except IntegrityError:
                raise ValidationError({"error_detail": "이미 사용된 파일의 url 입니다."})

    @extend_schema(summary="스터디 노트 상세 조회", tags=["StudyGroup"], responses={200: StudyNoteDetailSerializer})
    def get(self, request: Request, group_id: int, note_id: int) -> Response:
        note = self._get_note(group_id, note_id, prefetch=["attachments", "images"])
        serializer = StudyNoteDetailSerializer(note)
        return Response(serializer.data)

    @extend_schema(
        summary="스터디 노트 수정",
        tags=["StudyGroup"],
        request=StudyNoteUpdateSerializer,
        responses={200: StudyNoteUpdateResponseSerializer},
    )
    @transaction.atomic
    def patch(self, request: Request, group_id: int, note_id: int) -> Response:
        note = self._get_note(group_id, note_id, prefetch=["attachments", "images"])
        self._check_permission(note, cast(User, request.user))

        serializer = StudyNoteUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        note_updated = False
        if "title" in validated_data:
            note.title = validated_data["title"]
            note_updated = True
        if "content" in validated_data:
            note.content = validated_data["content"]
            note_updated = True

        if "images" in validated_data:
            self._update_images(note, validated_data["images"])

        if "files" in validated_data:
            self._update_attachments(note, validated_data["files"])

        if note_updated:
            note.save()

        response_serializer = StudyNoteUpdateResponseSerializer(note)
        return Response(response_serializer.data)

    @extend_schema(
        summary="스터디 노트 삭제",
        tags=["StudyGroup"],
        responses={200: inline_serializer(name="StudyNoteDeleteResponse", fields={"detail": serializers.CharField()})},
    )
    @transaction.atomic
    def delete(self, request: Request, group_id: int, note_id: int) -> Response:
        note = self._get_note(group_id, note_id)
        self._check_permission(note, cast(User, request.user))

        note.delete()
        return Response({"detail": "스터디 학습 기록 삭제에 성공했습니다."})
