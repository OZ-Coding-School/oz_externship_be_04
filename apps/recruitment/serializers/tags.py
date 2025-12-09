import re
from typing import Any, List

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.recruitment.models import Tag


class TagSerializer(serializers.ModelSerializer[Tag]):
    """태그 조회 및 등록"""

    class Meta:
        model = Tag
        fields = ["id", "name"]
        read_only_fields = ["id"]
        extra_kwargs: dict[str, dict[str, object]] = {"name": {"validators": []}}

    def validate_name(self, value: str) -> str:
        name = (value or "").strip()

        if not name:
            raise ValidationError("name은 필수 입니다.")

        if not 1 <= len(name) <= 20:
            raise ValidationError("태그 이름은 1자 이상 20자 이하로 입력해주세요")

        if not re.match(r"^[\w\s\-\u3131-\u318E\uAC00-\uD7A3]+$", name):
            raise ValidationError("태그 이름에 허용되지 않는 문자가 포함되어 있습니다.")

        return name

    def create(self, validated_data: Any) -> Tag:
        name = validated_data["name"]

        tag, created = Tag.objects.get_or_create(name=name)

        if not created:
            raise ValidationError({"error_detail": "이미 존재하는 태그입니다."})

        return tag


class RecruitmentTagUpdateSerializer(serializers.Serializer[Any]):
    """
    공고에 태그 목록을 작성 및 수정
    태그 최대 5개 적용
    """

    tags = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
        help_text="공고에 연결할 태그 ID 목록",
    )

    def validate_tags(self, value: List[int]) -> List[int]:

        if len(value) > 5:
            raise ValidationError("태그는 5개이상 등록 할수 없습니다.")

        if len(value) != len(set(value)):
            raise ValidationError("태그 ID는 중복될 수 없습니다.")

        return value
