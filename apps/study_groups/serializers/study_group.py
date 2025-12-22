from datetime import datetime
from typing import Any

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import GroupMember, StudyGroup, StudyLecture
from apps.users.models.users import User


# 스터디그룹
class StudyGroupSerializer(serializers.ModelSerializer[StudyGroup]):
    lectures = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        help_text="Lecture 목록(최대 5개)",
        max_length=5,
    )

    class Meta:
        model = StudyGroup
        fields = [
            "id",
            "name",
            "introduction",
            "max_headcount",
            "profile_img_url",
            "start_at",
            "end_at",
            "status",
            "lectures",
        ]
        read_only_fields = ["id", "status"]

    def validate_start_at(self, value: datetime) -> datetime:
        if value.date() < timezone.now().date():
            raise serializers.ValidationError("스터디 시작일은 오늘 이후여야 합니다.")
        return value

    def validate_end_at(self, value: datetime) -> datetime:
        start_at = self.initial_data.get("start_at")
        if start_at:
            start_date = datetime.fromisoformat(start_at).date()
            if (value.date() - start_date).days < 5:
                raise serializers.ValidationError("스터디 종료일은 시작일보다 최소 5일 이후여야 합니다.")
        return value

    def validate_lectures(self, value: list[int]) -> list[int]:
        if len(value) > 5:
            raise serializers.ValidationError("강의는 최대 5개까지 선택 가능합니다.")

        existing_ids = set(CrawledLecture.objects.filter(id__in=value).values_list("id", flat=True))
        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(f"존재하지 않는 강의 ID가 포함되어 있습니다: {sorted(missing_ids)}")
        return value

    def create(self, validated_data: dict[str, Any]) -> StudyGroup:
        lectures_data = validated_data.pop("lectures", [])
        study_group = StudyGroup.objects.create(**validated_data)

        if lectures_data:
            lectures = [
                StudyLecture(
                    study_group_id=study_group.id,
                    lecture_id=lecture_id,
                )
                for lecture_id in lectures_data
            ]
            StudyLecture.objects.bulk_create(lectures)

        request_user = self.context["request"].user
        if isinstance(request_user, AnonymousUser):
            raise serializers.ValidationError("로그인이 필요합니다.")

        GroupMember.objects.create(
            study_group_id=study_group,
            user_id=request_user,
            is_leader=True,
        )
        return study_group

    def update(self, instance: StudyGroup, validated_data: dict[str, Any]) -> StudyGroup:
        lectures_data = validated_data.pop("lectures", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lectures_data is not None:
            with transaction.atomic():
                StudyLecture.objects.filter(study_group_id=instance.id).delete()
                if lectures_data:
                    lectures = [
                        StudyLecture(
                            study_group_id=instance.id,
                            lecture_id=lecture_id,
                        )
                        for lecture_id in lectures_data
                    ]
                    StudyLecture.objects.bulk_create(lectures)
        return instance


class StudyGroupListSerializer(serializers.ModelSerializer[StudyGroup]):
    lectures = serializers.SerializerMethodField()
    current_headcount = serializers.SerializerMethodField()
    is_leader = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroup
        fields = [
            "id",
            "name",
            "is_leader",
            "start_at",
            "end_at",
            "max_headcount",
            "current_headcount",
            "profile_img_url",
            "status",
            "lectures",
            "reviews",
        ]

    def get_lectures(self, obj: StudyGroup) -> list[dict[str, Any]]:
        return [
            {"id": sl.lecture.id, "title": sl.lecture.title, "instructor": sl.lecture.instructor}
            for sl in obj.studylecture_study_groups.all()
        ]

    def get_current_headcount(self, obj: StudyGroup) -> int:
        return len(obj.groupmember_study_groups.all())

    def get_is_leader(self, obj: StudyGroup) -> bool:
        user = self.context["request"].user
        if not getattr(user, "is_authenticated", False):
            return False
        return any(m.user_id.id == user.id and m.is_leader for m in obj.groupmember_study_groups.all())

    def get_reviews(self, obj: StudyGroup) -> list[dict[str, Any]]:
        user = self.context["request"].user
        user_id = user.id if getattr(user, "is_authenticated", False) else None
        rvws = obj.review_study_groups.all()
        return [
            {
                "id": rvw.id,
                "is_mine": (rvw.user_id == user_id) if user_id is not None else False,
                "star_rating": rvw.star_rating,
                "content": rvw.content,
            }
            for rvw in rvws
        ]


class StudyGroupDetailSerializer(serializers.ModelSerializer[StudyGroup]):
    lectures = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    current_headcount = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroup
        fields = [
            "id",
            "name",
            "introduction",
            "profile_img_url",
            "start_at",
            "end_at",
            "max_headcount",
            "current_headcount",
            "status",
            "lectures",
            "members",
        ]

    def get_current_headcount(self, obj: StudyGroup) -> int:
        return len(obj.groupmember_study_groups.all())

    def get_lectures(self, obj: StudyGroup) -> list[dict[str, Any]]:
        study_lectures = obj.studylecture_study_groups.all()
        # 삭제된 강의는 제외하고 유효한 강의만 반환
        result = []
        for sl in study_lectures:
            # 강의 none 관련 오류 try-exceapt 예외처리
            try:
                lecture = getattr(sl, "lecture", None)
                if lecture is not None:
                    result.append(
                        {
                            "id": lecture.id,
                            "thumbnail_img_url": lecture.thumbnail_img_url,
                            "title": lecture.title,
                            "instructor": lecture.instructor,
                            "url_link": lecture.url_link,
                        }
                    )
            except (ObjectDoesNotExist, AttributeError):
                continue
        return result

    def get_members(self, obj: StudyGroup) -> list[dict[str, Any]]:
        members = obj.groupmember_study_groups.all().order_by("-is_leader")
        # 삭제된 사용자는 제외하고 유효한 멤버만 반환
        result = []
        for m in members:
            # getattr, try-except로 예외처리
            try:
                user = getattr(m, "user_id", None)
                if user is not None:
                    result.append(
                        {
                            "id": user.id,
                            "nickname": user.nickname,
                            "profile_img_url": user.profile_img_url,
                            "is_leader": m.is_leader,
                        }
                    )
            except (ObjectDoesNotExist, AttributeError):
                continue
        return result


class DelegateLeaderRequestSerializer(serializers.Serializer):  # type: ignore
    target_member_id = serializers.IntegerField()


class DetailResponseSerializer(serializers.Serializer):  # type: ignore
    detail = serializers.CharField()


class ErrorDetailResponseSerializer(serializers.Serializer):  # type: ignore
    error_detail = serializers.CharField()
