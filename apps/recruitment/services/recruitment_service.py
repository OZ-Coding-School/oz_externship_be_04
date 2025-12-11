from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Count, F, Q, QuerySet
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.recruitment.models import (
    Recruitment,
    RecruitmentAttachment,
    RecruitmentImage,
    RecruitmentTag,
    Tag,
)
from apps.users.models import User

ERROR_MESSAGES = {
    "RECRUITMENT_NOT_FOUND": "해당 공고를 찾을 수 없습니다.",
    "PERMISSION_DENIED": "권한이 없습니다.",
    "RECRUITMENT_CLOSED": "마감된 공고는 수정/삭제할 수 없습니다.",
}

SORT_OPTIONS = {
    "latest": "-created_at",
    "oldest": "created_at",
    "most_views": "-views_count",
    "most_bookmarks": "-bookmark_count",
}

DEFAULT_SORT = "latest"


class RecruitmentService:
    @staticmethod
    def _get_base_queryset(include_attachments: bool = False) -> QuerySet[Recruitment]:
        """
        QuerySet 반환

        Args:
            include_attachments: 첨부파일 포함 여부

        Returns:
            Recruitment QuerySet
        """
        queryset = (
            Recruitment.objects.select_related("study_group", "author")
            .prefetch_related(
                "images",
                "recruitment_tags__tag",
                "study_group__studylecture_set__lecture",
            )
            .annotate(bookmark_count=Count("recruitment_bookmarks"))
        )
        if include_attachments:
            queryset = queryset.prefetch_related("attachments")
        return queryset

    @staticmethod
    def _validate_author_permission(recruitment: Recruitment, user: User) -> None:
        """
        작성자 권한 및 공고 상태 검증

        Args:
            recruitment: 검증할 공고
            user: 요청 사용자

        Raises:
            PermissionDenied: 작성자가 아닌 경우
            ValidationError: 마감된 공고인 경우
        """
        if recruitment.author != user:
            raise PermissionDenied(ERROR_MESSAGES["PERMISSION_DENIED"])
        if recruitment.is_closed:
            raise ValidationError({"error_detail": ERROR_MESSAGES["RECRUITMENT_CLOSED"]})

    @staticmethod
    def _save_relations(
        recruitment: Recruitment,
        tags: list[Tag],
        files: list[dict[str, str]],
        image_urls: list[str],
    ) -> None:
        """
        연관 데이터(태그, 파일, 이미지) 저장

        Args:
            recruitment: 공고 객체
            tags: 태그 리스트
            files: 파일 정보 리스트
            image_urls: 이미지 URL 리스트
        """
        if tags:
            RecruitmentTag.objects.bulk_create(
                [RecruitmentTag(recruitment=recruitment, tag=tag) for tag in tags],
                ignore_conflicts=True,
            )
        if files:
            RecruitmentAttachment.objects.bulk_create(
                [
                    RecruitmentAttachment(
                        recruitment=recruitment,
                        file_name=f["file_name"],
                        file_url=f["file_url"],
                    )
                    for f in files
                ]
            )
        if image_urls:
            RecruitmentImage.objects.bulk_create(
                [RecruitmentImage(recruitment=recruitment, img_url=url) for url in image_urls]
            )

    @classmethod
    def get_filtered_recruitments(
        cls,
        base_filter: Q = Q(),
        search: Optional[str] = None,
        tags: Optional[str] = None,
        is_closed: Optional[str] = None,
        sort: str = DEFAULT_SORT,
        allow_oldest: bool = True,
    ) -> QuerySet[Recruitment]:
        """
        필터링 및 정렬된 공고 QuerySet 반환

        Args:
            base_filter: 기본 필터 조건
            search: 검색 키워드
            tags: 태그 (쉼표 구분)
            is_closed: 마감 여부
            sort: 정렬 옵션
            allow_oldest: oldest 정렬 허용 여부

        Returns:
            필터링 및 정렬된 QuerySet
        """
        queryset = cls._get_base_queryset().filter(base_filter)

        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(content__icontains=search))

        if tags:
            tag_list = [tag.strip() for tag in tags.split(",")]
            queryset = queryset.filter(recruitment_tags__tag__name__in=tag_list).distinct()

        if is_closed is not None:
            is_closed_bool = is_closed.lower() in ["true", "1", "yes"]
            queryset = queryset.filter(is_closed=is_closed_bool)

        sort_map = {k: v for k, v in SORT_OPTIONS.items() if allow_oldest or k != "oldest"}
        order_by = sort_map.get(sort, SORT_OPTIONS[DEFAULT_SORT])
        queryset = queryset.order_by(order_by)

        return queryset

    @classmethod
    @transaction.atomic
    def create_recruitment(cls, user: User, validated_data: dict[str, Any]) -> Recruitment:
        """
        공고 생성

        Args:
            user: 작성자
            validated_data: 검증된 공고 데이터

        Returns:
            생성된 Recruitment 객체
        """
        tags = validated_data.pop("tags", [])
        files = validated_data.pop("files", [])
        image_urls = validated_data.pop("image_urls", [])

        recruitment = Recruitment.objects.create(author=user, **validated_data)
        cls._save_relations(recruitment, tags, files, image_urls)

        return recruitment

    @classmethod
    def get_recruitment_detail(cls, uuid: UUID) -> Recruitment:
        """
        공고 상세 조회

        Args:
            uuid: 공고 UUID

        Returns:
            Recruitment 객체
        """
        queryset = cls._get_base_queryset(include_attachments=True).filter(uuid=uuid)
        recruitment = get_object_or_404(queryset)
        return recruitment

    @staticmethod
    def increment_view_count(uuid: UUID) -> None:
        """
        조회수 증가

        Args:
            uuid: 공고 UUID
        """
        Recruitment.objects.filter(uuid=uuid).update(views_count=F("views_count") + 1)

    @classmethod
    @transaction.atomic
    def update_recruitment(cls, uuid: UUID, user: User, validated_data: dict[str, Any]) -> Recruitment:
        """
        공고 수정

        Args:
            uuid: 공고 UUID
            user: 요청 사용자
            validated_data: 검증된 수정 데이터

        Returns:
            수정된 Recruitment 객체

        Raises:
            PermissionDenied: 권한 없음
            ValidationError: 마감된 공고
        """
        recruitment = get_object_or_404(cls._get_base_queryset(include_attachments=True), uuid=uuid)
        cls._validate_author_permission(recruitment, user)

        tags = validated_data.pop("tags", None)
        files = validated_data.pop("files", None)
        image_urls = validated_data.pop("image_urls", None)

        for attr, value in validated_data.items():
            setattr(recruitment, attr, value)
        recruitment.save()

        if tags is not None:
            RecruitmentTag.objects.filter(recruitment=recruitment).delete()
            if tags:
                cls._save_relations(recruitment, tags, [], [])

        if files is not None:
            RecruitmentAttachment.objects.filter(recruitment=recruitment).delete()
            if files:
                cls._save_relations(recruitment, [], files, [])

        if image_urls is not None:
            RecruitmentImage.objects.filter(recruitment=recruitment).delete()
            if image_urls:
                cls._save_relations(recruitment, [], [], image_urls)

        updated_recruitment = cls._get_base_queryset(include_attachments=True).get(uuid=uuid)
        return updated_recruitment

    @staticmethod
    def delete_recruitment(uuid: UUID, user: User) -> None:
        """
        공고 마감 (Soft Delete)

        Args:
            uuid: 공고 UUID
            user: 요청 사용자

        Raises:
            PermissionDenied: 권한 없음
            ValidationError: 마감된 공고
        """
        recruitment = get_object_or_404(Recruitment, uuid=uuid)
        RecruitmentService._validate_author_permission(recruitment, user)

        recruitment.is_closed = True
        recruitment.save(update_fields=["is_closed"])

    @staticmethod
    def build_update_response_data(recruitment: Recruitment) -> dict[str, Any]:
        """
        PATCH 응답 데이터 구성 (명세서 기준)

        Args:
            recruitment: 수정된 공고 객체 (prefetch 필요: recruitment_tags__tag, attachments, images)

        Returns:
            명세서에 맞춘 응답 dict
        """
        return {
            "uuid": str(recruitment.uuid),
            "title": recruitment.title,
            "content": recruitment.content,
            "estimated_fee": recruitment.estimated_fee,
            "expected_headcount": recruitment.expected_headcount,
            "tags": [{"id": rt.tag.id, "name": rt.tag.name} for rt in recruitment.recruitment_tags.all()],
            "files": [
                {"id": a.id, "file_name": a.file_name, "file_url": a.file_url} for a in recruitment.attachments.all()
            ],
            "image_urls": [img.img_url for img in recruitment.images.all()],
            "close_at": recruitment.close_at,
            "updated_at": recruitment.updated_at,
        }
