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

    def validate_name(self, value: str) -> str:

        # 태그 이름 길이 제한
        if not 1 <= len(value) <= 20:
            raise ValidationError("태그 이름은 1자 이상, 20자 이하 입니다.")

        return value


class RecruitmentTagUpdateSerializer(serializers.Serializer[Any]):
    """
    공고에 태그 목록을 작성 및 수정
    태그 최대 5개 적용
    """

    tags = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,  # 태그가 없는것도 허용
        help_text="공고에 연결할 태그 ID 목록",
    )

    def validate_tags(self, value: List[int]) -> List[int]:

        # 태그는 최대 5개까지 허용
        if len(value) > 5:
            raise ValidationError("태그는 5개이상 등록 할수 없습니다.")

        # 태그 ID 중복 여부 확인
        if len(value) != len(set(value)):
            raise ValidationError("태그 ID는 중복될 수 없습니다.")

        return value
