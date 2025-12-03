from datetime import datetime
from typing import Any

from rest_framework import serializers

from apps.lectures.models import CrawledLecture
from apps.study_groups.models import StudyGroup, StudyLecture


# 스터디그룹
class StudyGroupSerializer(serializers.ModelSerializer[StudyGroup]):
    # 강의 필드 임의 추가
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

    # 유효성 관련
    def validate_start_at(self, value: datetime) -> datetime:
        if value.date() < datetime.now().date():
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
        return value

    def create(self, validated_data: dict[str, Any]) -> StudyGroup:
        lectures_data = validated_data.pop("lectures", [])
        study_group = StudyGroup.objects.create(**validated_data)

        for lecture_id in lectures_data:
            StudyLecture.objects.create(
                study_group_id=study_group, lecture_id=CrawledLecture.objects.get(id=lecture_id)
            )
        return study_group

    def update(self, instance: StudyGroup, validated_data: dict[str, Any]) -> StudyGroup:
        lectures_data = validated_data.pop("lectures", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lectures_data is not None:
            StudyLecture.objects.filter(study_group_id=instance).delete()
            for lecture_id in lectures_data:
                StudyLecture.objects.create(
                    study_group_id=instance, lecture_id=CrawledLecture.objects.get(id=lecture_id)
                )
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
        return obj.groupmember_set.filter(user_id=user, is_leader=True).exists()


# 상세정보 조회용
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
        return [{"nickname": m.user_id, "is_leader": m.is_leader} for m in members]
