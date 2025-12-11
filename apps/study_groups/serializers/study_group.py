from datetime import datetime
from typing import Any

from django.db import transaction
from rest_framework import serializers

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import StudyGroup, StudyLecture


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
        ### datetime() vs. timezone.now()
        # https://jongseoung.tistory.com/257
        # 학습 후 택1하여 유지 or 수정할 것
        if value.date() < datetime.now().date():
            raise serializers.ValidationError("스터디 시작일은 오늘 이후여야 합니다.")
        return value

    def validate_end_at(self, value: datetime) -> datetime:
        ### datetime() vs. timezone.now()
        # https://jongseoung.tistory.com/257
        # 학습 후 택1하여 유지 or 수정할 것
        start_at = self.initial_data.get("start_at")
        if start_at:
            start_date = datetime.fromisoformat(start_at).date()
            if (value.date() - start_date).days < 5:
                raise serializers.ValidationError("스터디 종료일은 시작일보다 최소 5일 이후여야 합니다.")
        return value

    def validate_lectures(self, value: list[int]) -> list[int]:
        if len(value) > 5:
            raise serializers.ValidationError("강의는 최대 5개까지 선택 가능합니다.")

        ### 해당 ID가 CrawledLecture 모델에 실제로 존재하는지에 대한 DB 유효성 검증 로직
        existing_ids = set(CrawledLecture.objects.filter(id__in=value).values_list("id", flat=True))

        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(f"존재하지 않는 강의 ID가 포함되어 있습니다: {sorted(missing_ids)}")
        ###
        return value

    def create(self, validated_data: dict[str, Any]) -> StudyGroup:
        lectures_data = validated_data.pop("lectures", [])
        study_group = StudyGroup.objects.create(**validated_data)

        ### for문 -> bulk_create로 DB 최적화하기
        ### https://gardeny.tistory.com/15
        if lectures_data:
            lectures = [
                StudyLecture(
                    study_group_id=study_group.id,
                    lecture_id=lecture_id,
                )
                for lecture_id in lectures_data
            ]
            StudyLecture.objects.bulk_create(lectures)
        return study_group

    def update(self, instance: StudyGroup, validated_data: dict[str, Any]) -> StudyGroup:
        lectures_data = validated_data.pop("lectures", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        ### bulk_create
        if lectures_data is not None:
            with transaction.atomic():  # 주의: transaction 추가하여 원자성 보장
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
    member_count = serializers.SerializerMethodField()
    is_leader = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroup
        fields = [
            "id",
            "name",
            "member_count",
            "is_leader",
            "profile_img_url",
            "start_at",
            "end_at",
            "status",
            "lectures",
        ]

    def get_lectures(self, obj: StudyGroup) -> list[dict[str, Any]]:
        return [{"title": sl.lecture.title, "instructor": sl.lecture.instructor} for sl in obj.studylecture_set.all()]

    def get_member_count(self, obj: StudyGroup) -> str:
        return f"{obj.groupmember_set.count()} / {obj.max_headcount}"

    def get_is_leader(self, obj: StudyGroup) -> bool:
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        return obj.groupmember_set.filter(user_id=user.id, is_leader=True).exists()


class StudyGroupDetailSerializer(serializers.ModelSerializer[StudyGroup]):
    lectures = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    class Meta:
        model = StudyGroup
        fields = [
            "id",
            "name",
            "introduction",
            "profile_img_url",
            "start_at",
            "end_at",
            "status",
            "lectures",
            "members",
        ]

    def get_lectures(self, obj: StudyGroup) -> list[dict[str, Any]]:
        return [
            {
                "thumbnail": sl.lecture.thumbnail_img_url,
                "title": sl.lecture.title,
                "instructor": sl.lecture.instructor,
                "url": sl.lecture.url_link,
            }
            for sl in obj.studylecture_set.all()
        ]

    def get_members(self, obj: StudyGroup) -> list[dict[str, Any]]:
        members = obj.groupmember_set.all().order_by("-is_leader")
        return [{"nickname": m.user_id.nickname, "is_leader": m.is_leader} for m in members]


class DelegateLeaderRequestSerializer(serializers.Serializer[Any]):
    target_member_id = serializers.IntegerField()


class DetailResponseSerializer(serializers.Serializer[Any]):
    detail = serializers.CharField()


class ErrorDetailResponseSerializer(serializers.Serializer[Any]):
    error_detail = serializers.CharField()
